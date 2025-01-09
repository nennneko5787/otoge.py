__all__ = (
    "CSRFTokenNotFound",
    "LoginFailed",
    "WrongFormat",
    "RequestFailed",
)


class CSRFTokenNotFound(Exception):
    pass


class LoginFailed(Exception):
    pass


class WrongFormat(Exception):
    pass


class RequestFailed(Exception):
    pass


class RequiresPremium(Exception):
    pass
