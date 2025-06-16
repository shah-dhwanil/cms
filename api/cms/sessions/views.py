from typing import Annotated
from fastapi import Request
from uuid import UUID
from cms.sessions.repository import SessionRepository
from cms.sessions.exceptions import SessionNotFoundException
from cms.sessions.utils import get_client_ip
from cms.users.models import UserNotFoundExceptionResponse
from cms.users.exceptions import UserNotFoundException
from cms.utils.hash import hash_string
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Path, Response
from fastapi import status
from asyncpg import Connection

from cms.sessions.models import (
    CreateSessionRequest,
    CreateSessionResponse,
    ListSessionResponse,
    Session,
    SessionNotFoundExceptionResponse,
)

__all__ = [
    "router",
    "create_session",
    "get_session_by_id",
    "get_sessions_by_user_id",
    "terminate_session",
    "terminate_user_all_sessions",
    "clean_expired_sessions",
]

router = APIRouter(prefix="/session", tags=["sessions"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": CreateSessionResponse,
            "description": "Session created successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": UserNotFoundExceptionResponse,
            "description": "User not found.",
        },
    },
)
async def create_session(
    body: Annotated[CreateSessionRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    request: Request,
    response: Response,
):
    try:
        session = await SessionRepository.create(
            connection,
            body.user_id,
            hash_string(get_client_ip(request)),
        )
        response.status_code = status.HTTP_201_CREATED
        return CreateSessionResponse(
            session_id=session["session_id"], expires_at=session["expires_at"]
        )
    except UserNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotFoundExceptionResponse(context=e.context)


@router.get(
    "/{session_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": Session,
            "description": "Session details retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": SessionNotFoundExceptionResponse,
            "description": "Session not found.",
        },
    },
)
async def get_session_by_id(
    session_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        record = await SessionRepository.get_by_id(connection, session_id)
        response.status_code = status.HTTP_200_OK
        return Session(
            session_id=record["session_id"],
            user_id=record["user_id"],
            ip_address=record["ip_addr"],
            expires_at=record["expires_at"],
            is_terminated=record["is_terminated"],
        )
    except SessionNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return SessionNotFoundExceptionResponse(context=e.context)


@router.get(
    "/user/{user_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListSessionResponse,
            "description": "User sessions retrieved successfully.",
        },
    },
)
async def get_sessions_by_user_id(
    user_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    records = await SessionRepository.get_by_user_id(connection, user_id)
    response.status_code = status.HTTP_200_OK
    return ListSessionResponse(
        sessions=[
            Session(
                session_id=record["session_id"],
                user_id=record["user_id"],
                ip_address=record["ip_addr"],
                expires_at=record["expires_at"],
                is_terminated=record["is_terminated"],
            )
            for record in records
        ]
    )


@router.delete(
    "/clean",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Hard delete of expired sessions successfully.",
        },
    },
)
async def clean_expired_sessions(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    await SessionRepository.clean_expired(connection)
    response.status_code = status.HTTP_204_NO_CONTENT
    return


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Session terminated successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": SessionNotFoundExceptionResponse,
            "description": "Session not found.",
        },
    },
)
async def terminate_session(
    session_id: Annotated[UUID, Path()],
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


@router.delete(
    "/user/{user_id}/all",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "All user sessions terminated successfully.",
        },
    },
)
async def terminate_user_all_sessions(
    user_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    await SessionRepository.terminate_all_user_sessions(connection, user_id)
    response.status_code = status.HTTP_204_NO_CONTENT
    return
