from typing import Annotated
from asyncpg import Connection, Path
from cms.auth.dependency import PermissionRequired
from cms.auth.schemas import CredentialsNotFoundResponse, NotAuthorizedResponse
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Response, status

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

router = APIRouter(
    prefix="/permissions",
    tags=["permissions"],
    responses={
        401: {"model": CredentialsNotFoundResponse},
        403: {"model": NotAuthorizedResponse},
    },
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionRequired(["permissions:create:any"]))],
    responses={
        201: {"model": None},
        409: {"model": PermissionAlreadyExistsResponse},
    },
)
async def create_permission(
    permission: Annotated[CreatePermissionRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await PermissionRepository.create(
            connection, permission.name, permission.description
        )
        response.status_code = 201
        return
    except PermissionAlreadyExists as e:
        response.status_code = 409
        return PermissionAlreadyExistsResponse(context=e.context)


@router.get(
    "/",
    dependencies=[Depends(PermissionRequired(["permissions:read:any"]))],
    responses={200: {"model": list[GetPermissionResponse]}},
)
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
    dependencies=[Depends(PermissionRequired(["permissions:delete:any"]))],
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
