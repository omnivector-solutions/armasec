from __future__ import annotations

from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

import httpx
import pydantic
import snick
import typer
from loguru import logger

from armasec_cli.exceptions import Abort
from armasec_cli.config import Settings


def build_client(settings: Settings):
    protocol = "https" if settings.oidc_use_https else "http"
    base_url = f"{protocol}://{settings.oidc_domain}"
    logger.debug(f"Creating client with base URL {base_url}")
    return httpx.Client(
        base_url=base_url,
        headers={"content-type": "application/x-www-form-urlencoded"},
    )


def attach_client(func):
    @wraps(func)
    def wrapper(ctx: typer.Context, *args, **kwargs):
        if ctx.obj.settings is None:
            raise Abort(
                """
                Cannot attach client before settings!

                Check the order of the decorators and make sure settings are attached
                first.
                """,
                subject="Attaching out of order",
                log_message="Attaching out of order",
            )

        logger.debug("Binding client to CLI context")
        ctx.obj.client = build_client(ctx.obj.settings)
        return func(ctx, *args, **kwargs)

    return wrapper


def _deserialize_request_model(
    request_model: pydantic.BaseModel,
    request_kwargs: dict[str, Any],
    abort_message: str,
    abort_subject: str,
):
    """
    Deserialize a pydantic model instance into request_kwargs for a request in place.
    """
    Abort.require_condition(
        all(
            [
                "data" not in request_kwargs,
                "json" not in request_kwargs,
                "content" not in request_kwargs,
            ]
        ),
        snick.unwrap(
            f"""
            {abort_message}:
            Request was incorrectly structured.
            """
        ),
        raise_kwargs=dict(
            subject=abort_subject,
            log_message=snick.unwrap(
                """
                When using `request_model`, you may not pass
                `data`, `json`, or `content` in the `request_kwargs`
                """
            ),
        ),
    )
    with Abort.handle_errors(
        snick.unwrap(
            f"""
            {abort_message}:
            Request data could not be deserialized for http request.
            """
        ),
        raise_kwargs=dict(
            subject=abort_subject,
            log_message=snick.unwrap(
                f"""
                Could not deserialize instance of {request_model.__class__}:
                {request_model}
                """
            ),
        ),
    ):
        request_kwargs["content"] = request_model.model_dump_json()
        request_kwargs["headers"] = {"Content-Type": "application/json"}


ResponseModel = TypeVar("ResponseModel", bound=pydantic.BaseModel)


def make_request(
    client: httpx.Client,
    url_path: str,
    method: str,
    *,
    expected_status: int | None = None,
    expect_response: bool = True,
    abort_message: str = "There was an error communicating with the API",
    abort_subject: str = "REQUEST FAILED",
    response_model_cls: type[ResponseModel] | None = None,
    request_model: pydantic.BaseModel | None = None,
    save_to_file: Path | None = None,
    **request_kwargs,
) -> ResponseModel | dict | int:
    """
    Make a request against the Jobbergate API.

    Args:
        url_path:            The path to add to the base url of the client where the
                             request should be sent
        method:              The REST method to use for the request
                             (GET, PUT, UPDATE, POST, DELETE, etc)
        expected_status:     The status code to expect on the response. If it is not
                             received, raise an Abort
        expect_response:     Indicates if response data (JSON) is expected from the API
                             endpoint
        abort_message:       The message to show the user if there is a problem and the
                             app must be aborted
        abort_subject:       The subject to use in Abort output to the user
        response_model_cls:  If supplied, serialize the response data into this Pydantic
                             model class
        request_model:       Use a pydantic model instance as the data body for the
                             request
        request_kwargs:      Any additional keyword arguments that need to be passed on
                             to the client
    """

    if request_model is not None:
        _deserialize_request_model(
            request_model,
            request_kwargs,
            abort_message,
            abort_subject,
        )

    logger.debug(f"Making request to url_path={url_path}")
    request = client.build_request(method, url_path, **request_kwargs)

    # Look for the request body in the request_kwargs
    debug_request_body = request_kwargs.get(
        "data",
        request_kwargs.get("json", request_kwargs.get("content")),
    )
    logger.debug(
        snick.dedent(
            f"""
            Request built with:
              url:     {request.url}
              method:  {method}
              headers: {request.headers}
              body:    {debug_request_body}
            """
        )
    )

    with Abort.handle_errors(
        snick.unwrap(
            f"""
            {abort_message}:
            Communication with the API failed.
            """
        ),
        raise_kwargs=dict(
            subject=abort_subject,
            log_message="There was an error making the request to the API",
        ),
    ):
        response = client.send(request)

    if expected_status is not None and response.status_code != expected_status:
        if (
            method in ("PATCH", "PUT", "DELETE")
            and response.status_code == 403
            and "does not own" in response.text
        ):
            raise Abort(
                snick.dedent(
                    f"""
                     {abort_message}:
                     [red]You do not own this resource.[/red]
                     Please contact the owner if you need it to be modified.
                     """,
                ),
                subject=abort_subject,
                log_message=snick.unwrap(
                    f"""
                    Resource could not be modified by non-owner:
                    {response.text}
                    """
                ),
            )
        else:
            raise Abort(
                snick.unwrap(
                    f"""
                    {abort_message}:
                    Received an error response.
                    """
                ),
                subject=abort_subject,
                log_message=snick.unwrap(
                    f"""
                    Got an error code for request:
                    {response.status_code}:
                    {response.text}
                    """
                ),
            )

    if save_to_file is not None:
        save_to_file.parent.mkdir(parents=True, exist_ok=True)
        save_to_file.write_bytes(response.content)
        return response.status_code

    # TODO: constrain methods with a named enum
    if expect_response is False or method == "DELETE":
        return response.status_code

    with Abort.handle_errors(
        snick.unwrap(
            f"""
            {abort_message}:
            Response carried no data.
            """
        ),
        raise_kwargs=dict(
            subject=abort_subject,
            log_message=f"Failed unpacking json: {response.text}",
        ),
    ):
        data = response.json()
    logger.debug(f"Extracted data from response: {data}")

    if response_model_cls is None:
        return data

    logger.debug("Validating response data with ResponseModel")
    with Abort.handle_errors(
        snick.unwrap(
            f"""
            {abort_message}:
            Unexpected data in response.
            """
        ),
        raise_kwargs=dict(
            subject=abort_subject,
            log_message=f"Unexpected format in response data: {data}",
        ),
    ):
        return response_model_cls(**data)
