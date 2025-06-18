from typing import Annotated, Optional
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Path, Query, Response
from cms.permissions.repository import PermissionRepository
from fastapi import status
from asyncpg import Connection

from cms.permissions.exceptions import (
    PermissionAlreadyExistsException,
    PermissionNotFoundException,
    PermissionStillReferencedException,
)
from cms.permissions.models import (
    CreatePermissionRequest,
    ListPermissionResponse,
    Permission,
    PermissionAlreadyExistsExceptionResponse,
    PermissionNotFoundExceptionResponse,
    PermissionStillReferencedExceptionResponse,
    UpdatePermissionRequest,
)
from cms.auth.dependency import RequiresPermission
from cms.auth.models import (
    CredentialsNotFoundExceptionResponse,
    NotAuthorizedExceptionResponse,
)

__all__ = [
    "router",
    "create_permission",
    "get_all_permissions",
    "get_permission_by_slug",
    "update_permission",
    "delete_permission",
]

router = APIRouter(
    prefix="/permission",
    tags=["permissions"],
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
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(RequiresPermission("permission:create"))],
    responses={
        status.HTTP_204_NO_CONTENT: {
            "description": "Permission created successfully.",
        },
        status.HTTP_409_CONFLICT: {
            "model": PermissionAlreadyExistsExceptionResponse,
            "description": "Permission with the given slug already exists.",
        },
    },
)
async def create_permission(
    body: Annotated[CreatePermissionRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await PermissionRepository.create(connection, body.slug, body.description)
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    except PermissionAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return PermissionAlreadyExistsExceptionResponse(context=e.context)


@router.get(
    "/",
    dependencies=[Depends(RequiresPermission("permission:read"))],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListPermissionResponse,
            "description": "List of permissions",
        },
    },
)
async def get_all_permissions(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
    offset: Annotated[Optional[int], Query()] = 0,
    limit: Annotated[Optional[int], Query()] = 100,
):
    records = await PermissionRepository.get_all(connection, limit, offset)
    response.status_code = status.HTTP_200_OK
    return ListPermissionResponse(
        permissions=[
            Permission(
                slug=record["slug"],
                description=record["description"],
            )
            for record in records
        ]
    )


@router.get(
    "/{slug}",
    dependencies=[Depends(RequiresPermission("permission:read"))],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": Permission,
            "description": "Permission details retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": PermissionNotFoundExceptionResponse,
            "description": "Permission not found.",
        },
    },
)
async def get_permission_by_slug(
    slug: Annotated[str, Path(max_length=64)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        record = await PermissionRepository.get_by_slug(connection, slug)
        response.status_code = status.HTTP_200_OK
        return Permission(
            slug=record["slug"],
            description=record["description"],
        )
    except PermissionNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return PermissionNotFoundExceptionResponse(context=e.context)


@router.patch(
    "/{slug}",
    dependencies=[Depends(RequiresPermission("permission:update"))],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Permission updated successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": PermissionNotFoundExceptionResponse,
            "description": "Permission not found.",
        },
    },
)
async def update_permission(
    slug: Annotated[str, Path(max_length=64)],
    body: Annotated[UpdatePermissionRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await PermissionRepository.update(connection, slug, body.description)
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    except PermissionNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return PermissionNotFoundExceptionResponse(context=e.context)


@router.delete(
    "/{slug}",
    dependencies=[Depends(RequiresPermission("permission:delete"))],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Permission deleted successfully.",
        },
        status.HTTP_409_CONFLICT: {
            "model": PermissionStillReferencedExceptionResponse,
            "description": "Permission is still referenced by other entities.",
        },
    },
)
async def delete_permission(
    slug: Annotated[str, Path(max_length=64)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await PermissionRepository.delete(connection, slug)
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    except PermissionStillReferencedException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return PermissionStillReferencedExceptionResponse(
            slug=slug,
            context=e.context,
        )
