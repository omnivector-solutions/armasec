import buzz
import starlette.status


class ArmasecError(buzz.Buzz):
    """
    A custom exception class used for checking conditions and handling other exceptions.

    Attributes:
        status_code: The HTTP status code indicated by the error. Set to 400.
    """

    status_code: int = starlette.status.HTTP_400_BAD_REQUEST


class AuthenticationError(ArmasecError):
    """
    Indicates a failure to authenticate and decode jwt.

    Attributes:
        status_code: The HTTP status code indicated by the error. Set to 401.
    """

    status_code: int = starlette.status.HTTP_401_UNAUTHORIZED


class AuthorizationError(ArmasecError):
    """
    Indicates that the provided claims don't match the claims required for a protected endpoint.

    Attributes:
        status_code: The HTTP status code indicated by the error. Set to 403.
    """

    status_code: int = starlette.status.HTTP_403_FORBIDDEN
