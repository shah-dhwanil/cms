from typing import Annotated
from uuid import UUID
from asyncpg import Connection, Path
from cms.auth.exceptions import NotAuthorized
from fastapi import APIRouter, Body, Depends, Response, status
from cms.utils.postgres import PgPool
from cms.users.exceptions import UserDoesNotExists
from cms.staff.exceptions import StaffAlreadyExists, StaffDoesNotExists
from cms.users.schemas import UserDoesNotExistsResponse
from cms.staff.schemas import (
    CreateStaffRequest,
    GetStaffResponse,
    UpdateStaffRequest,
    StaffAlreadyExistsResponse,
    StaffDoesNotExistsResponse,
)
from cms.staff.repository import StaffRepository
from cms.auth.dependency import PermissionRequired, get_user_id
from cms.auth.schemas import NotAuthorizedResponse, CredentialsNotFoundResponse

router = APIRouter(
    prefix="/staff",
    tags=["staff"],
    responses={
        401: {"model": CredentialsNotFoundResponse},
        403: {"model": NotAuthorizedResponse},
    },
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionRequired(["staff:create:any"]))],
    responses={
        404: {"model": UserDoesNotExistsResponse},
        409: {"model": StaffAlreadyExistsResponse},
    },
)
async def create_staff(
    staff: Annotated[CreateStaffRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await StaffRepository.create(
            connection,
            staff.user_id,
            staff.first_name,
            staff.last_name,
            staff.position,
            staff.education,
            staff.experience,
            staff.activity,
            staff.other_details,
            staff.public,
        )
    except UserDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserDoesNotExistsResponse(context=e.context)
    except StaffAlreadyExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StaffAlreadyExistsResponse(context=e.context)


@router.get(
    "/",
    dependencies=[Depends(PermissionRequired(["staff:read:any"]))],
    responses={
        200: {"model": GetStaffResponse},
    },
)
async def get_staff(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    result = await StaffRepository.get_all(connection)
    response.status_code = status.HTTP_200_OK
    return [
        GetStaffResponse(
            user_id=staff["id"],
            first_name=staff["first_name"],
            last_name=staff["last_name"],
            position=staff["position"],
            education=staff["education"],
            experience=staff["experience"],
            activity=staff["activity"],
            other_details=staff["other_details"],
            public=staff["public"],
            active=staff["active"],
        )
        for staff in result
    ]


@router.get(
    "/{id}",
    responses={
        200: {"model": GetStaffResponse},
        404: {"model": StaffDoesNotExistsResponse},
    },
)
async def get_staff_details(
    id: Annotated[UUID, Path()],
    user_permission: Annotated[
        list[str],
        Depends(
            PermissionRequired(
                ["staff:read:any"], ["staff:read:public"], ["staff:read:self"]
            )
        ),
    ],
    user_id: Annotated[UUID, Depends(get_user_id)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if "staff:read:self" in user_permission and id != user_id:
        raise NotAuthorized()
    try:
        result = await StaffRepository.get_by_id(connection, id)
        if (
            "staff:read:public" in user_permission
            and not result["public"]
            and not result["active"]
        ):
            raise NotAuthorized()
        response.status_code = status.HTTP_200_OK
        return GetStaffResponse(
            user_id=result["id"],
            first_name=result["first_name"],
            last_name=result["last_name"],
            position=result["position"],
            education=result["education"],
            experience=result["experience"],
            activity=result["activity"],
            other_details=result["other_details"],
            public=result["public"],
            active=result["active"],
        )
    except StaffDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StaffDoesNotExistsResponse(context=e.context)


@router.patch(
    "/{id}",
    responses={
        200: {"model": GetStaffResponse},
        404: {"model": StaffDoesNotExistsResponse},
    },
)
async def update_staff(
    id: Annotated[UUID, Path()],
    staff: Annotated[UpdateStaffRequest, Body()],
    user_permission: Annotated[
        list[str],
        Depends(PermissionRequired(["staff:update:any"], ["staff:update:self"])),
    ],
    user_id: Annotated[UUID, Depends(get_user_id)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    print(staff)
    if "staff:update:self" in user_permission and id != user_id:
        raise NotAuthorized()
    try:
        await StaffRepository.update(
            connection,
            id,
            staff.first_name,
            staff.last_name,
            staff.position,
            staff.education,
            staff.experience,
            staff.activity,
            staff.other_details,
            staff.public,
        )
        response.status_code = status.HTTP_200_OK
        return
    except StaffDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StaffDoesNotExistsResponse(context=e.context)


@router.delete(
    "/{id}",
    dependencies=[Depends(PermissionRequired(["staff:delete:any"]))],
    responses={
        200: {"model": GetStaffResponse},
        404: {"model": StaffDoesNotExistsResponse},
    },
)
async def delete_staff(
    id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await StaffRepository.delete(connection, id)
        response.status_code = status.HTTP_200_OK
        return
    except StaffDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StaffDoesNotExistsResponse(context=e.context)
