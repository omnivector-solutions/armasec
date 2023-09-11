import pendulum
import plummet
import pytest
from jose import jwt
from typer import Context

from cli.schemas import CliContext


@pytest.fixture
def make_token():
    """
    Provide a fixture that returns a helper function for creating an access_token for testing.
    """

    def _helper(azp: str = None, email: str = None, expires=plummet.AGGREGATE_TYPE) -> str:
        """
        Create an access_token with a given user email, org name, and expiration moment.
        """
        expires_moment: pendulum.DateTime = plummet.momentize(expires)

        extra_claims = dict()
        if azp is not None:
            extra_claims["azp"] = azp
        if email is not None:
            extra_claims["email"] = email

        return jwt.encode(
            {
                "exp": expires_moment.int_timestamp,
                **extra_claims,
            },
            "fake-secret",
            algorithm="HS256",
        )

    return _helper



@pytest.fixture
def override_cache_dir(tmp_path, mocker):
    with mocker.patch("cli.cache.cache_dir", new=tmp_path):
        token_path = tmp_path / "token"
        token_path.mkdir()
        yield


@pytest.fixture
def mock_context(mocker):
    typer_context = Context(mocker.MagicMock())
    typer_context.obj = CliContext()
    return typer_context
