from typing import Annotated
from uuid import UUID

from argon2 import PasswordHasher
from asyncpg import Connection
from fastapi import Body, Depends, FastAPI, Path, Query, Response, status
from uuid_utils.compat import uuid7

from cms.users.exceptions import UserAlreadyExists, UserNotExists
from cms.users.repository import UserRepository
from cms.users.schemas import (
    CreateUserRequest,
    CreateUserResponse,
    DeleteUserResponse,
    GetUserRequest,
    GetUserResponse,
    UpdatePasswordRequest,
    UpdatePasswordResponse,
    UpdateUserRequest,
    UpdateUserResponse,
    UserAlreadyExistsResponse,
    UserNotExistsResponse,
)
from cms.utils.config import Config
from cms.utils.postgres import PgPool

app = FastAPI(
    title="Users",
    version="0.0.1",
)


@app.post(
    "/",
    tags=["users"],
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": CreateUserResponse},
        409: {"model": UserAlreadyExistsResponse},
    },
)
async def create_user(
    user: Annotated[CreateUserRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    config = Config.get_config()
    argon2 = PasswordHasher(
        time_cost=config.ARGON_TIME_COST,
        memory_cost=config.ARGON_MEMORY_COST,
        parallelism=config.ARGON_PARALLELISM,
        hash_len=config.ARGON_HASH_LENGTH,
        salt_len=config.ARGON_SALT_LENGTH,
    )
    hashed_password = argon2.hash(user.password)
    uid = uuid7()
    try:
        await UserRepository.create(
            connection,
            uid=uid,
            email_id=user.email_id,
            contact_no=user.contact_no,
            password=hashed_password,
            profile_image=user.profile_image,
        )
        response.status_code = status.HTTP_201_CREATED
        return CreateUserResponse(id=uid)
    except UserAlreadyExists as e:
        response.status_code = status.HTTP_409_CONFLICT
        return UserAlreadyExistsResponse(context=e.context)


@app.get(
    "/",
    tags=["users"],
    responses={200: {"model": GetUserResponse}, 404: {"model": UserNotExistsResponse}},
)
async def get_user(
    user: Annotated[GetUserRequest, Query()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        if user.email_id is not None:
            result = await UserRepository.get_by_email_id(connection, user.email_id)
        elif user.id is not None:
            result = await UserRepository.get_by_id(connection, user.id)
        else:
            return
        response.status_code = status.HTTP_200_OK
        return GetUserResponse.model_construct(
            id=result["id"],
            email_id=result["email_id"],
            contact_no=result["contact_no"],
            profile_image=result["profile_image"],
        )
    except UserNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotExistsResponse(context=e.context)


@app.patch(
    "/{id}",
    tags=["users"],
    responses={
        200: {"model": UpdateUserResponse},
        404: {"model": UserNotExistsResponse},
    },
)
async def update_user(
    id: Annotated[UUID, Path()],
    user: Annotated[UpdateUserRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await UserRepository.update(
            connection,
            id,
            password=None,
            contact_no=user.contact_no,
            profile_image=user.profile_image,
        )
        response.status_code = status.HTTP_200_OK
        return UpdateUserResponse()
    except UserNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotExistsResponse(context=e.context)


@app.patch(
    "/{id}/update_password/",
    tags=["users"],
    responses={
        200: {"model": UpdatePasswordResponse},
        404: {"model": UserNotExistsResponse},
    },
)
async def update_password(
    id: Annotated[UUID, Path()],
    user: Annotated[UpdatePasswordRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    config = Config.get_config()
    argon2 = PasswordHasher(
        time_cost=config.ARGON_TIME_COST,
        memory_cost=config.ARGON_MEMORY_COST,
        parallelism=config.ARGON_PARALLELISM,
        hash_len=config.ARGON_HASH_LENGTH,
        salt_len=config.ARGON_SALT_LENGTH,
    )
    hashed_password = argon2.hash(user.new_password)
    try:
        await UserRepository.update(
            connection,
            id,
            password=hashed_password,
            contact_no=None,
            profile_image=None,
        )
        response.status_code = status.HTTP_200_OK
        return UpdatePasswordResponse()
    except UserNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotExistsResponse(context=e.context)


@app.delete(
    "/{id}",
    tags=["users"],
    responses={
        200: {"model": DeleteUserResponse},
        404: {"model": UserNotExistsResponse},
    },
)
async def delete_user(
    id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await UserRepository.delete(connection, id)
        response.status_code = status.HTTP_200_OK
        return DeleteUserResponse()
    except UserNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotExistsResponse(context=e.context)
