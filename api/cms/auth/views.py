from typing import Annotated
from cms.auth.dependency import get_session_id
from cms.auth.schemas import LoginRequest, LoginResponse
from cms.utils.postgres import PgPool
from cms.users.repository import UserRepository
from cms.users.exceptions import UserNotExists
from cms.users.schemas import UserNotExistsResponse
from cms.sessions.repository import SessionRepository
from cms.sessions.exceptions import SessionDoesNotExists
from cms.sessions.schemas import SessionDoesNotExistsResponse
from cms.utils.config import Config
from asyncpg import Connection
from uuid import UUID


from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Body, Depends, Response, status

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    responses={
        200: {"model": LoginResponse},
        404: {"model": UserNotExistsResponse},
        403: {"model": SessionDoesNotExistsResponse},
    },
)
async def login(
    user: Annotated[LoginRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        result = await UserRepository.get_by_email_id(connection, user.email_id)
    except UserNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotExistsResponse(context=e.context)
    config = Config.get_config()
    argon2 = PasswordHasher(
        time_cost=config.ARGON_TIME_COST,
        memory_cost=config.ARGON_MEMORY_COST,
        parallelism=config.ARGON_PARALLELISM,
        hash_len=config.ARGON_HASH_LENGTH,
        salt_len=config.ARGON_SALT_LENGTH,
    )
    try:
        argon2.verify(result["password"], user.password)
    except VerifyMismatchError:
        ...
    session = await SessionRepository.create_session(connection, result["id"])
    return LoginResponse(token=session)


@router.post(
    "/logout",
    responses={200: {"model": None}, 404: {"model": SessionDoesNotExistsResponse}},
)
async def logout(
    session_id: Annotated[UUID, Depends(get_session_id)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await SessionRepository.revoke_session(connection, session_id)
    except SessionDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return SessionDoesNotExistsResponse(context=e.context)
    return
