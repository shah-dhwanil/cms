from typing import Annotated, Optional
from uuid import UUID

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
from cms.staff.exceptions import (
    StaffAlreadyExistsException,
    StaffNotFoundException,
)
from cms.staff.models import (
    CreateStaffRequest,
    CreateStaffResponse,
    ListStaffResponse,
    Staff,
    StaffAlreadyExistsExceptionResponse,
    StaffNotFoundExceptionResponse,
    UpdateStaffRequest,
)
from cms.staff.repository import StaffRepository
from cms.users.exceptions import UserAlreadyExistsException
from cms.users.repository import UserRepository
from cms.utils.argon2 import hash_password
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Path, Query, Response, status

__all__ = [
    "router",
    "create_staff",
    "get_all_staff",
    "get_public_staff",
    "get_staff_by_id",
    "update_staff",
    "delete_staff",
]

router = APIRouter(
    prefix="/staff",
    tags=["staff"],
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
    dependencies=[Depends(RequiresPermission("staff:create"))],
    responses={
        status.HTTP_201_CREATED: {
            "model": CreateStaffResponse,
            "description": "Staff created successfully.",
        },
        status.HTTP_409_CONFLICT: {
            "model": StaffAlreadyExistsExceptionResponse,
            "description": "Staff with the given detail already exists.",
        },
    },
)
async def create_staff(
    body: Annotated[CreateStaffRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    async with connection.transaction():
        try:
            async with connection.transaction():
                user_id = await UserRepository.create(
                    connection,
                    body.email_id,
                    hash_password("Staff@123"),
                    body.contact_no,
                )
        except UserAlreadyExistsException as e:
            if e.context["parameter"] == "email_id":
                user = await UserRepository.get_by_email_id(connection, body.email_id)
            elif e.context["parameter"] == "contact_no":
                user = await UserRepository.get_by_contact_no(
                    connection, body.contact_no
                )
            else:
                raise e
            user_id = user["id"]
        try:
            staff_id = await StaffRepository.create(
                connection,
                user_id=user_id,
                first_name=body.first_name,
                last_name=body.last_name,
                position=body.position,
                education=body.education,
                experience=body.experience,
                activity=body.activity,
                other_details=body.other_details,
                is_public=body.is_public,
            )
            response.status_code = status.HTTP_201_CREATED
            return CreateStaffResponse(staff_id=staff_id)
        except StaffAlreadyExistsException as e:
            response.status_code = status.HTTP_409_CONFLICT
            return StaffAlreadyExistsExceptionResponse(context=e.context)


@router.get(
    "/",
    dependencies=[Depends(RequiresPermission("staff:read:any"))],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListStaffResponse,
            "description": "List of all staff members",
        },
    },
)
async def get_all_staff(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
    offset: Annotated[Optional[int], Query()] = 0,
    limit: Annotated[Optional[int], Query()] = 100,
):
    records = await StaffRepository.get_all(connection, limit, offset)
    response.status_code = status.HTTP_200_OK
    return ListStaffResponse(
        staff=[
            Staff(
                id=record["id"],
                first_name=record["first_name"],
                last_name=record["last_name"],
                email_id=record["email_id"],
                contact_no=record["contact_no"],
                position=record["position"],
                education=record["education"],
                experience=record["experience"],
                activity=record["activity"],
                other_details=record["other_details"],
                is_public=record["is_public"],
            )
            for record in records
        ]
    )


@router.get(
    "/public",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListStaffResponse,
            "description": "List of public staff members",
        },
    },
)
async def get_public_staff(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
    offset: Annotated[Optional[int], Query()] = 0,
    limit: Annotated[Optional[int], Query()] = 100,
):
    records = await StaffRepository.get_all_public_staff(connection, limit, offset)
    response.status_code = status.HTTP_200_OK
    return ListStaffResponse(
        staff=[
            Staff(
                id=record["id"],
                first_name=record["first_name"],
                last_name=record["last_name"],
                email_id=record["email_id"],
                contact_no=record["contact_no"],
                position=record["position"],
                education=record["education"],
                experience=record["experience"],
                activity=record["activity"],
                other_details=record["other_details"],
                is_public=record["is_public"],
            )
            for record in records
        ]
    )


@router.get(
    "/{staff_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": Staff,
            "description": "Staff details retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": StaffNotFoundExceptionResponse,
            "description": "Staff not found.",
        },
    },
)
async def get_staff_by_id(
    staff_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(RequiresAnyOfGivenPermission(["staff:read:any"], ["staff:read:self"])),
    ],
    response: Response,
):
    # Check if staff is accessing their own data or has permission to read any staff
    if "staff:read:self" in permissions and staff_id != session.user.user_id:
        raise NotEnoughPermissionsException()

    try:
        record = await StaffRepository.get_by_id(connection, staff_id)
        response.status_code = status.HTTP_200_OK
        return Staff(
            id=record["id"],
            first_name=record["first_name"],
            last_name=record["last_name"],
            email_id=record["email_id"],
            contact_no=record["contact_no"],
            position=record["position"],
            education=record["education"],
            experience=record["experience"],
            activity=record["activity"],
            other_details=record["other_details"],
            is_public=record["is_public"],
        )
    except StaffNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StaffNotFoundExceptionResponse(context=e.context)


@router.patch(
    "/{staff_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Staff updated successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": StaffNotFoundExceptionResponse,
            "description": "Staff not found.",
        },
    },
)
async def update_staff(
    staff_id: Annotated[UUID, Path()],
    body: Annotated[UpdateStaffRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(["staff:update:any"], ["staff:update:self"])
        ),
    ],
    response: Response,
):
    # Check if staff is updating their own data or has permission to update any staff
    if "staff:update:self" in permissions and staff_id != session.user.user_id:
        raise NotEnoughPermissionsException()

    try:
        await StaffRepository.update(
            connection,
            staff_id,
            first_name=body.first_name,
            last_name=body.last_name,
            position=body.position,
            education=body.education,
            experience=body.experience,
            activity=body.activity,
            other_details=body.other_details,
            is_public=body.is_public,
        )
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    except StaffNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StaffNotFoundExceptionResponse(context=e.context)


@router.delete(
    "/{staff_id}",
    dependencies=[Depends(RequiresPermission("staff:delete"))],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Staff deleted successfully.",
        },
    },
)
async def delete_staff(
    staff_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    await StaffRepository.delete(connection, staff_id)
    response.status_code = status.HTTP_204_NO_CONTENT
    return
