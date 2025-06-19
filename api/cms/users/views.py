from typing import Annotated, Optional, Union
from uuid import UUID

from argon2.exceptions import VerifyMismatchError
from asyncpg import Connection
from cms.auth.dependency import (
    RequiresAnyOfGivenPermission,
    RequiresPermission,
    get_session,
)
from cms.auth.exceptions import NotEnoughPermissionsException
from cms.auth.models import (
    CredentialsNotFoundExceptionResponse,
    NotAuthorizedExceptionResponse,
    Session,
)
from cms.permissions.exceptions import PermissionNotFoundException
from cms.permissions.models import PermissionNotFoundExceptionResponse
from cms.users.exceptions import UserAlreadyExistsException, UserNotFoundException
from cms.users.models import (
    CreateUserRequest,
    CreateUserResponse,
    GrantPermissionRequest,
    ListUserPermissionsResponse,
    ListUserResponse,
    PasswordIncorrectExceptionResponse,
    RevokePermissionRequest,
    UpdateUserPasswordRequest,
    UpdateUserRequest,
    User,
    UserAlreadyExistsExceptionResponse,
    UserNotFoundExceptionResponse,
)
from cms.users.repository import UserRepository
from cms.utils.argon2 import hash_password, verify_password
from cms.utils.minio import MinioClient
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Path, Query, Response, UploadFile, status
from fastapi.params import File
from pydantic import EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber

__all__ = [
    "router",
    "create_user",
    "get_all_users",
    "get_user_by_id",
    "get_user_by_email_id",
    "update_user",
    "update_user_password",
    "delete_user",
    "grant_user_permissions",
    "revoke_user_permissions",
    "get_user_permissions",
]

router = APIRouter(
    prefix="/user",
    tags=["users"],
    responses={
        status.HTTP_401_UNAUTHORIZED: {
            "model": CredentialsNotFoundExceptionResponse,
            "description": "Credentials not found or invalid.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": NotAuthorizedExceptionResponse,
            "description": "User is not authorized to perform this action.",
        },
    },
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(RequiresPermission("user:create"))],
    responses={
        status.HTTP_201_CREATED: {
            "model": CreateUserResponse,
            "description": "User created successfully.",
        },
        status.HTTP_409_CONFLICT: {
            "model": UserAlreadyExistsExceptionResponse,
            "description": "User with the given detail already exists.",
        },
    },
)
async def create_user(
    body: Annotated[CreateUserRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    hashed_password = hash_password(body.password)
    try:
        uid = await UserRepository.create(
            connection,
            body.email_id.lower(),
            hashed_password,
            body.contact_no,
            body.profile_image_id,
        )
        response.status_code = status.HTTP_201_CREATED
        return CreateUserResponse(user_id=uid)
    except UserAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return UserAlreadyExistsExceptionResponse(context=e.context)


@router.get(
    "/",
    dependencies=[Depends(RequiresPermission("user:read:any"))],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListUserResponse,
            "description": "List of users",
        },
    },
)
async def get_all_users(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
    offset: Annotated[Optional[int], Query()] = 0,
    limit: Annotated[Optional[int], Query()] = 100,
):
    records = await UserRepository.get_all(connection, limit, offset)
    response.status_code = status.HTTP_200_OK
    return ListUserResponse(
        users=[
            User(
                user_id=record["id"],
                email_id=record["email_id"],
                contact_no=record["contact_no"],
                profile_image_id=record["profile_image_id"],
            )
            for record in records
        ]
    )


@router.get(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": User,
            "description": "User details retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": UserNotFoundExceptionResponse,
            "description": "User not found.",
        },
    },
)
async def get_user_by_id(
    user_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(RequiresAnyOfGivenPermission(["user:read:any"], ["user:read:self"])),
    ],
    response: Response,
):
    # Check if user is accessing their own data or has permission to read any user
    if "user:read:self" in permissions and user_id != session.user.user_id:
        raise NotEnoughPermissionsException()

    try:
        record = await UserRepository.get_by_id(connection, user_id)
        response.status_code = status.HTTP_200_OK
        return User(
            user_id=record["id"],
            email_id=record["email_id"],
            contact_no=record["contact_no"],
            profile_image_id=record["profile_image_id"],
        )
    except UserNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotFoundExceptionResponse(context=e.context)


@router.get(
    "/by_email/{email_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": User,
            "description": "User details retrieved successfully by email.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": UserNotFoundExceptionResponse,
            "description": "User not found by email.",
        },
    },
)
async def get_user_by_email_id(
    email_id: Annotated[EmailStr, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(RequiresAnyOfGivenPermission(["user:read:any"], ["user:read:self"])),
    ],
    response: Response,
):
    try:
        record = await UserRepository.get_by_email_id(connection, email_id.lower())
        if "user:read:self" in permissions and record["id"] != session.user.user_id:
            raise NotEnoughPermissionsException()
        response.status_code = status.HTTP_200_OK
        return User(
            user_id=record["id"],
            email_id=record["email_id"],
            contact_no=record["contact_no"],
            profile_image_id=record["profile_image_id"],
        )
    except UserNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotFoundExceptionResponse(context=e.context)


@router.get(
    "/by_contact_no/{contact_no}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": User,
            "description": "User details retrieved successfully by email.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": UserNotFoundExceptionResponse,
            "description": "User not found by email.",
        },
    },
)
async def get_user_by_contact_no(
    contact_no: Annotated[PhoneNumber, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(RequiresAnyOfGivenPermission(["user:read:any"], ["user:read:self"])),
    ],
    response: Response,
):
    try:
        record = await UserRepository.get_by_contact_no(connection, contact_no)
        if "user:read:self" in permissions and record["id"] != session.user.user_id:
            raise NotEnoughPermissionsException()
        response.status_code = status.HTTP_200_OK
        return User(
            user_id=record["id"],
            email_id=record["email_id"],
            contact_no=record["contact_no"],
            profile_image_id=record["profile_image_id"],
        )
    except UserNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotFoundExceptionResponse(context=e.context)


@router.patch(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "User updated successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": UserNotFoundExceptionResponse,
            "description": "User not found.",
        },
    },
)
async def update_user(
    user_id: Annotated[UUID, Path()],
    body: Annotated[UpdateUserRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(["user:update:any"], ["user:update:self"])
        ),
    ],
    response: Response,
):
    # Check if user is updating their own data or has permission to update any user
    if "user:update:self" in permissions and user_id != session.user.user_id:
        return NotEnoughPermissionsException()

    try:
        await UserRepository.update(
            connection,
            user_id,
            None,
            body.contact_no,
            body.profile_image_id,
        )
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    except UserNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotFoundExceptionResponse(context=e.context)


@router.patch(
    "/{user_id}/password",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "User password updated successfully.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "model": PasswordIncorrectExceptionResponse,
            "description": "Current password is incorrect.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": UserNotFoundExceptionResponse,
            "description": "User not found.",
        },
    },
)
async def update_user_password(
    user_id: Annotated[UUID, Path()],
    body: Annotated[UpdateUserPasswordRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(["user:update:any"], ["user:update:self"])
        ),
    ],
    response: Response,
):
    if "user:update:self" in permissions and user_id != session.user.user_id:
        raise NotEnoughPermissionsException()
    try:
        record = await UserRepository.get_by_id(connection, user_id)
        verify_password(record["password"], body.current_password)
        hashed_password = hash_password(body.new_password)
        await UserRepository.update(connection, user_id, hashed_password, None, None)
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    except VerifyMismatchError:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PasswordIncorrectExceptionResponse(context=dict())
    except UserNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotFoundExceptionResponse(context=e.context)


@router.patch(
    "/{user_id}/profile_image",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "User profile image updated successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": UserNotFoundExceptionResponse,
            "description": "User not found.",
        },
    },
)
async def update_user_profile_image(
    user_id: Annotated[UUID, Path()],
    file: Annotated[UploadFile, File()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(["user:update:any"], ["user:update:self"])
        ),
    ],
    response: Response,
):
    # Check if user is updating their own data or has permission to update any user
    if "user:update:self" in permissions and user_id != session.user.user_id:
        raise NotEnoughPermissionsException()
    async with MinioClient.get_client() as client:
        result = await client.put_object(
            bucket_name="profile-img",
            object_name=str(user_id),
            data=file,
            length=file.size,
            content_type=file.content_type,
            metadata={
                "file_name": file.filename,
            },
        )
    try:
        await UserRepository.update(
            connection,
            user_id,
            None,
            None,
            result.version_id,
        )
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    except UserNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotFoundExceptionResponse(context=e.context)


@router.delete(
    "/{user_id}",
    dependencies=[Depends(RequiresPermission("user:delete"))],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "User deleted successfully.",
        },
    },
)
async def delete_user(
    user_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    await UserRepository.delete(connection, user_id)
    response.status_code = status.HTTP_204_NO_CONTENT
    return


@router.post(
    "/{user_id}/permissions/grant",
    dependencies=[Depends(RequiresPermission("user:grant_permission"))],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Permissions granted successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": Union[
                UserNotFoundExceptionResponse, PermissionNotFoundExceptionResponse
            ],
            "description": "Resource not found.",
        },
    },
)
async def grant_user_permissions(
    user_id: Annotated[UUID, Path()],
    body: Annotated[GrantPermissionRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await UserRepository.grant_permissions(connection, user_id, body.permissions)
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    except UserNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotFoundExceptionResponse(context=e.context)
    except PermissionNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return PermissionNotFoundExceptionResponse(context=e.context)


@router.post(
    "/{user_id}/permissions/revoke",
    dependencies=[Depends(RequiresPermission("user:revoke_permission"))],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Permissions revoked successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": UserNotFoundExceptionResponse,
            "description": "User not found.",
        },
    },
)
async def revoke_user_permissions(
    user_id: Annotated[UUID, Path()],
    body: Annotated[RevokePermissionRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await UserRepository.revoke_permissions(connection, user_id, body.permissions)
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    except UserNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotFoundExceptionResponse(context=e.context)


@router.get(
    "/{user_id}/permissions",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListUserPermissionsResponse,
            "description": "User permissions retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": UserNotFoundExceptionResponse,
            "description": "User not found.",
        },
    },
)
async def get_user_permissions(
    user_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(
                ["user_permission:read:any"], ["user_permission:read:self"]
            )
        ),
    ],
    response: Response,
):
    if "user_permission:read:self" in permissions and user_id != session.user.user_id:
        raise NotEnoughPermissionsException()
    try:
        records = await UserRepository.get_user_permissions(connection, user_id)
        response.status_code = status.HTTP_200_OK
        return ListUserPermissionsResponse(
            permissions=[record["permission"] for record in records]
        )
    except UserNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserNotFoundExceptionResponse(context=e.context)
