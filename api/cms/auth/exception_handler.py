from cms.auth.models import (
    CredentialsNotFoundExceptionResponse,
    NotAuthorizedExceptionResponse,
)
from fastapi.responses import JSONResponse
from fastapi import status


async def credentials_not_found_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content=CredentialsNotFoundExceptionResponse(context=exc.context).model_dump(),
    )


async def session_invalid_or_expired_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=NotAuthorizedExceptionResponse(context=exc.context).model_dump(),
    )


async def not_enough_permissions_exception_handler(request, exc):
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content=NotAuthorizedExceptionResponse(context=exc.context).model_dump(),
    )
