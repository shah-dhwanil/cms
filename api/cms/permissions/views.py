from typing import Annotated, Optional
from asyncpg import Connection, Path
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Response, status
from aiofile import async_open

from cms.permissions.schemas import (
    CreatePermissionRequest,
    GetPermissionResponse,
    PermissionAlreadyExistsResponse,
    PermissionDoesNotExistResponse,
    PermissionReferencedResponse,
)
from cms.permissions.exceptions import (
    PermissionAlreadyExists,
    PermissionReferenced,
    PermissionDoesNotExist,
)
from cms.permissions.repository import PermissionRepository

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    responses={
        201: {"model": None},
        409: {"model": PermissionAlreadyExistsResponse},
    },
)
async def create_permission(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
    permission: Annotated[Optional[CreatePermissionRequest], Body()] = None,
):
    if permission is not None:
        try:
            await PermissionRepository.create(
                connection, permission.name, permission.description
            )
            response.status_code = 201
            return
        except PermissionAlreadyExists as e:
            response.status_code = 409
            return PermissionAlreadyExistsResponse(context=e.context)

    available_permissions = set(
        map(
            lambda permission: permission["name"],
            await PermissionRepository.get_all(connection),
        )
    )
    async with async_open("./cms/permissions/permissions.json", "r") as fp:
        default_permission = GetPermissionResponse.model_validate_json(await fp.read())
    for i in default_permission.permissions:
        if i.name not in available_permissions:
            await PermissionRepository.create(connection, i.name, i.description)
    response.status_code = 201
    return


@router.get("/", responses={200: {"model": list[GetPermissionResponse]}})
async def get_permissions(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
):
    result = await PermissionRepository.get_all(connection)
    return GetPermissionResponse(
        permissions=list(
            map(
                lambda permission: GetPermissionResponse.Permission(
                    name=permission["name"], description=permission["description"]
                ),
                result,
            )
        )
    )


@router.delete(
    "/{permission_name}",
    responses={
        200: {"model": None},
        404: {"model": PermissionDoesNotExistResponse},
        409: {"model": PermissionReferencedResponse},
    },
)
async def delete_permission(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
    permission_name: Annotated[str, Path()],
):
    try:
        await PermissionRepository.delete(connection, permission_name)
        response.status_code = status.HTTP_200_OK
        return
    except PermissionDoesNotExist as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return PermissionDoesNotExistResponse(context=e.context)
    except PermissionReferenced as e:
        response.status_code = status.HTTP_409_CONFLICT
        return PermissionReferencedResponse(context=e.context)
