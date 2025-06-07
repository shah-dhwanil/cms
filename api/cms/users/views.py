from typing import Annotated
from uuid import UUID

from argon2 import PasswordHasher
from asyncpg import Connection
from fastapi import APIRouter, Body, Depends, Path, Query, Response, status
from uuid_utils.compat import uuid7

from cms.auth.dependency import PermissionRequired, get_user_id
from cms.auth.exceptions import NotEnoughPermissions
from cms.auth.schemas import CredentialsNotFoundResponse, NotAuthorizedResponse
from cms.permissions.exceptions import PermissionDoesNotExist
from cms.permissions.schemas import (
    PermissionDoesNotExistResponse,
)
from cms.users.exceptions import UserAlreadyExists, UserDoesNotExists
from cms.users.repository import UserRepository
from cms.users.schemas import (
    CreateUserRequest,
    CreateUserResponse,
    GetUserPermissionResponse,
    GetUserRequest,
    GetUserResponse,
    GrantPermissionsRequest,
    RevokePermissionsRequest,
    UpdatePasswordRequest,
    UpdateUserRequest,
    UserAlreadyExistsResponse,
    UserDoesNotExistsResponse,
)
from cms.utils.config import Config
from cms.utils.postgres import PgPool

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={
        401: {"model": CredentialsNotFoundResponse},
        403: {"model": NotAuthorizedResponse},
    },
)


@router.post(
    "/",
    dependencies=[Depends(PermissionRequired(["users:create:any"]))],
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


@router.get(
    "/",
    responses={
        200: {"model": GetUserResponse},
        404: {"model": UserDoesNotExistsResponse},
    },
)
async def get_user(
    user: Annotated[GetUserRequest, Query()],
    user_permission: Annotated[
        list[str], Depends(PermissionRequired(["users:read:any"], ["users:read:self"]))
    ],
    user_id: Annotated[UUID, Depends(get_user_id)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if "users:read:self" in user_permission and user.id != user_id:
        raise NotEnoughPermissions()
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
    except UserDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserDoesNotExistsResponse(context=e.context)


@router.patch(
    "/{id}",
    responses={
        200: {"model": None},
        404: {"model": UserDoesNotExistsResponse},
    },
)
async def update_user(
    id: Annotated[UUID, Path()],
    user: Annotated[UpdateUserRequest, Body()],
    user_permission: Annotated[
        list[str],
        Depends(PermissionRequired(["users:update:any"], ["users:update:self"])),
    ],
    user_id: Annotated[UUID, Depends(get_user_id)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if "users:update:self" in user_permission and id != user_id:
        raise NotEnoughPermissions()
    try:
        await UserRepository.update(
            connection,
            id,
            password=None,
            contact_no=user.contact_no,
            profile_image=user.profile_image,
        )
        response.status_code = status.HTTP_200_OK
        return
    except UserDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserDoesNotExistsResponse(context=e.context)


@router.patch(
    "/{id}/update_password/",
    responses={
        200: {"model": None},
        404: {"model": UserDoesNotExistsResponse},
    },
)
async def update_password(
    id: Annotated[UUID, Path()],
    user: Annotated[UpdatePasswordRequest, Body()],
    user_id: Annotated[UUID, Depends(get_user_id)],
    user_permission: Annotated[
        list[str],
        Depends(PermissionRequired(["users:update:any"], ["users:update:self"])),
    ],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if "users:update:self" in user_permission and id != user_id:
        raise NotEnoughPermissions()
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
        return
    except UserDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserDoesNotExistsResponse(context=e.context)


@router.delete(
    "/{id}",
    dependencies=[Depends(PermissionRequired(["users:delete:any"]))],
    responses={
        200: {"model": None},
        404: {"model": UserDoesNotExistsResponse},
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
        return
    except UserDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserDoesNotExistsResponse(context=e.context)


@router.post(
    "/{id}/grant_permissions/",
    dependencies=[Depends(PermissionRequired(["permissions:grant:any"]))],
    tags=["permissions"],
    responses={
        200: {"model": None},
        400: {"model": PermissionDoesNotExistResponse},
        404: {"model": UserDoesNotExistsResponse},
    },
)
async def grant_permissions(
    id: Annotated[UUID, Path()],
    permissions: Annotated[GrantPermissionsRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await UserRepository.grant_permissions(connection, id, permissions.permissions)
    except UserDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserDoesNotExistsResponse(context=e.context)
    except PermissionDoesNotExist as e:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PermissionDoesNotExistResponse(context=e.context)
    response.status_code = status.HTTP_200_OK


@router.post(
    "/{id}/revoke_permissions/",
    dependencies=[Depends(PermissionRequired(["permissions:revoke:any"]))],
    tags=["permissions"],
    responses={200: {"model": None}},
)
async def revoke_permissions(
    id: Annotated[UUID, Path()],
    permissions: Annotated[RevokePermissionsRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    await UserRepository.revoke_permissions(connection, id, permissions.permissions)
    response.status_code = status.HTTP_200_OK


@router.get(
    "/{id}/permissions/",
    tags=["permissions"],
    responses={200: {"model": GetUserPermissionResponse}},
)
async def get_permissions(
    id: Annotated[UUID, Path()],
    user_permission: Annotated[
        list[str],
        Depends(
            PermissionRequired(
                ["users:read:any", "permissions:read:any"],
                ["users:read:self", "permissions:read:any"],
            )
        ),
    ],
    user_id: Annotated[UUID, Depends(get_user_id)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if "users:read:self" in user_permission and id != user_id:
        raise NotEnoughPermissions()
    result = await UserRepository.get_user_permissions(connection, id)
    response.status_code = status.HTTP_200_OK
    return GetUserPermissionResponse(
        permissions=list(map(lambda x: x["permission_name"], result))
    )
