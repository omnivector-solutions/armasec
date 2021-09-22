import buzz
import starlette.status


class ArmasecError(buzz.Buzz):
    """
    A custom exception class used for checking conditions and handling other exceptions.
    """

    status_code = starlette.status.HTTP_400_BAD_REQUEST


class AuthenticationError(ArmasecError):
    """
    Indicates a failure to authenticate and decode jwt.
    """

    status_code = starlette.status.HTTP_401_UNAUTHORIZED


class AuthorizationError(ArmasecError):
    """
    Indicates that the provided claims don't match the claims required for a protected endpoint.
    """

    status_code = starlette.status.HTTP_403_FORBIDDEN
