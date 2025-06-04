from cms.auth.schemas import CredentialsNotFoundResponse, NotAuthorizedResponse
from cms.utils.exceptions import BaseException
from fastapi import status
from fastapi.responses import JSONResponse


class CredentialsNotFound(BaseException):
    slug = "credentials_not_found"
    description = "Authentication Credentials not found"


class NotAuthorized(BaseException):
    slug = "not_authorized"
    description = "Your are not authorized to perform the action"


class SessionInvalidOrExpired(NotAuthorized):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__({"reason": "Session is invalid or expired", **kwargs}, *args)


class NotEnoughPermissions(NotAuthorized):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__({"reason": "Not enough permissions", **kwargs}, *args)


async def credentials_not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=CredentialsNotFoundResponse(context=exc.context).model_dump(),
    )


async def session_invalid_or_expired_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=NotAuthorizedResponse(context=exc.context).model_dump(),
    )


async def not_enough_permissions_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=NotAuthorizedResponse(context=exc.context).model_dump(),
    )
