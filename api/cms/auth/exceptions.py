from cms.utils.exceptions import CMSException


class CredentialsNotFoundException(CMSException):
    slug = "credentials_not_found"
    description = "Authentication Credentials not found"


class _NotAuthorizedException(CMSException):
    slug = "not_authorized"
    description = "Your are not authorized to perform the action"


class SessionInvalidOrExpiredException(_NotAuthorizedException):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__({"reason": "Session is invalid or expired", **kwargs}, *args)


class NotEnoughPermissionsException(_NotAuthorizedException):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__({"reason": "Not enough permissions", **kwargs}, *args)
