from typing import Annotated, Optional
from uuid import UUID
from asyncpg import Connection, Path
from cms.auth.dependency import PermissionRequired
from cms.auth.exceptions import NotEnoughPermissions
from cms.auth.schemas import CredentialsNotFoundResponse, NotAuthorizedResponse
from cms.sessions.exceptions import SessionDoesNotExists
from cms.users.schemas import UserNotExistsResponse
from cms.users.exceptions import UserNotExists
from cms.utils.postgres import PgPool
from cms.sessions.repository import SessionRepository
from cms.sessions.schemas import (
    CreateSessionRequest,
    CreateSessionsResponse,
    GetSessionResponse,
    SessionDoesNotExistsResponse,
)
from fastapi import APIRouter, Body, Depends, Query, Response, status

router = APIRouter(
    prefix="/session",
    tags=["Session"],
    responses={
        401: {"model": CredentialsNotFoundResponse},
        403: {"model": NotAuthorizedResponse},
    },
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionRequired(["session:create:any"]))],
    responses={
        201: {"model": CreateSessionsResponse},
        404: {"model": UserNotExistsResponse},
    },
)
async def create_session(
    user: Annotated[CreateSessionRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        session_id = await SessionRepository.create_session(connection, user.user_id)
        response.status_code = status.HTTP_201_CREATED
        return CreateSessionsResponse(session_id=session_id)
    except UserNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotExistsResponse(context=e.context)


@router.get(
    "/",
    responses={
        200: {"model": list[GetSessionResponse]},
        404: {"model": SessionDoesNotExistsResponse},
    },
)
async def get_session(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    user_permissions: Annotated[
        list[str],
        Depends(PermissionRequired(["session:read:all"], ["session:read:any"])),
    ],
    response: Response,
    session_id: Annotated[Optional[UUID], Query()] = None,
):
    if "session:read:any" in user_permissions and session_id is None:
        raise NotEnoughPermissions()
    result = []
    if session_id is not None:
        try:
            session = await SessionRepository.get_session(connection, session_id)
            result.append(
                GetSessionResponse(
                    session_id=session["id"],
                    user_id=session["user_id"],
                    created_at=str(session["created_at"]),
                    expires_at=str(session["expires_at"]),
                    revoked=session["revoked"],
                )
            )
        except SessionDoesNotExists as e:
            response.status_code = status.HTTP_404_NOT_FOUND
            return SessionDoesNotExistsResponse(context=e.context)
    else:
        sessions = await SessionRepository.get_all_sessions(connection)
        result = list(
            map(
                lambda x: GetSessionResponse(
                    session_id=x["id"],
                    user_id=x["user_id"],
                    created_at=str(x["created_at"]),
                    expires_at=str(x["expires_at"]),
                    revoked=x["revoked"],
                ),
                sessions,
            )
        )
    response.status_code = status.HTTP_200_OK
    return result


@router.post(
    "/{session_id}/revoke",
    dependencies=[Depends(PermissionRequired(["session:revoke:any"]))],
    responses={200: {"model": None}, 404: {"model": SessionDoesNotExistsResponse}},
)
async def revoke_session(
    session_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await SessionRepository.revoke_session(connection, session_id)
        response.status_code = status.HTTP_200_OK
        return
    except SessionDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return SessionDoesNotExistsResponse(context=e.context)
