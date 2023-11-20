from http import HTTPStatus

import buzz


class ArmasecError(buzz.Buzz):
    """
    A custom exception class used for checking conditions and handling other exceptions.

    Attributes:
        status_code: The HTTP status code indicated by the error. Set to 400.
    """

    status_code: int = HTTPStatus.BAD_REQUEST


class AuthenticationError(ArmasecError):
    """
    Indicates a failure to authenticate and decode jwt.

    Attributes:
        status_code: The HTTP status code indicated by the error. Set to 401.
    """

    status_code: int = HTTPStatus.NOT_FOUND


class AuthorizationError(ArmasecError):
    """
    Indicates that the provided claims don't match the claims required for a protected endpoint.

    Attributes:
        status_code: The HTTP status code indicated by the error. Set to 403.
    """

    status_code: int = HTTPStatus.FORBIDDEN


class PayloadMappingError(ArmasecError):
    """
    Indicates that the configured payload_claim_mapping did not match a path in the token.

    Attributes:
        status_code: The HTTP status code indicated by the error. Set to 500.
    """

    status_code: int = HTTPStatus.INTERNAL_SERVER_ERROR
