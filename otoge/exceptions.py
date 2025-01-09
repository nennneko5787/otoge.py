__all__ = (
    "CSRFTokenNotFound",
    "LoginFailed",
    "WrongFormat",
    "RequestFailed",
    "RequiresCardRegistration",
    "RequiresPlayData",
    "RequiresPremium",
)


class CSRFTokenNotFound(Exception):
    pass


class LoginFailed(Exception):
    pass


class WrongFormat(Exception):
    pass


class RequestFailed(Exception):
    pass


class RequiresCardRegistration(Exception):
    pass


class RequiresPlayData(Exception):
    pass


class RequiresPremium(Exception):
    pass
