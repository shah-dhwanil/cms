from typing import Annotated
from uuid import UUID
from cms.auth.dependency import get_session_id
from fastapi import APIRouter, Body, Depends, Response, Request
from fastapi import status
from asyncpg import Connection
from argon2.exceptions import VerifyMismatchError
from cms.users.repository import UserRepository
from cms.users.exceptions import UserNotFoundException
from cms.users.models import (
    UserNotFoundExceptionResponse,
    PasswordIncorrectExceptionResponse,
)
from cms.sessions.repository import SessionRepository
from cms.sessions.exceptions import SessionNotFoundException
from cms.sessions.models import SessionNotFoundExceptionResponse
from cms.sessions.utils import get_client_ip
from cms.utils.argon2 import verify_password
from cms.utils.hash import hash_string
from cms.utils.postgres import PgPool

from cms.auth.models import (
    LoginRequest,
    LoginResponse,
    RefreshSessionResponse,
)

__all__ = [
    "router",
    "login",
    "logout",
]

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": LoginResponse,
            "description": "Login successful.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": PasswordIncorrectExceptionResponse,
            "description": "Invalid credentials.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": UserNotFoundExceptionResponse,
            "description": "User not found.",
        },
    },
)
async def login(
    body: Annotated[LoginRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    request: Request,
    response: Response,
):
    try:
        # Get user by email
        user_record = await UserRepository.get_by_email_id(
            connection, body.email_id.lower()
        )

        # Verify password
        verify_password(user_record["password"], body.password)

        # Create session
        session = await SessionRepository.create(
            connection,
            user_record["id"],
            hash_string(get_client_ip(request)),
        )

        # Get user permissions
        permissions_records = await UserRepository.get_user_permissions(
            connection, user_record["id"]
        )
        permissions = [record["permission"] for record in permissions_records]

        response.status_code = status.HTTP_200_OK
        return LoginResponse(
            session_id=session["session_id"],
            user=LoginResponse.User(
                user_id=user_record["id"],
                profile_image_id=user_record["profile_image_id"],
                permissions=permissions,
            ),
            expires_at=session["expires_at"],
        )
    except UserNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotFoundExceptionResponse(context=e.context)
    except VerifyMismatchError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PasswordIncorrectExceptionResponse(context={})


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Logout successful.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": SessionNotFoundExceptionResponse,
            "description": "Session not found.",
        },
    },
)
async def logout(
    session_id: Annotated[UUID, Depends(get_session_id)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await SessionRepository.terminate(connection, session_id)
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    except SessionNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return SessionNotFoundExceptionResponse(context=e.context)


@router.post(
    "/refresh",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": LoginResponse,
            "description": "Session refreshed successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": SessionNotFoundExceptionResponse,
            "description": "Session not found.",
        },
    },
)
async def refresh_session(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session_id: Annotated[UUID, Depends(get_session_id)],
    response: Response,
):
    # Extend session expiration
    try:
        expires_at = await SessionRepository.refresh(connection, session_id)
        response.status_code = status.HTTP_200_OK
        return RefreshSessionResponse(
            session_id=session_id,
            expires_at=expires_at,
        )
    except SessionNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return SessionNotFoundExceptionResponse(context=e.context)
