from typing import Annotated, Optional, Union
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
from cms.departments.exceptions import (
    DepartmentAlreadyExistsException,
    DepartmentNotFoundException,
)
from cms.departments.models import (
    CreateDepartmentRequest,
    CreateDepartmentResponse,
    Department,
    DepartmentAlreadyExistsExceptionResponse,
    DepartmentNotFoundExceptionResponse,
    ListDepartmentResponse,
    UpdateDepartmentRequest,
)
from cms.departments.repository import DepartmentRepository
from cms.schools.exceptions import SchoolNotFoundException
from cms.schools.models import SchoolNotFoundExceptionResponse
from cms.staff.exceptions import StaffNotFoundException
from cms.staff.models import ListStaffResponse, Staff, StaffNotFoundExceptionResponse
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Path, Query, Response, status

__all__ = [
    "router",
    "create_department",
    "get_departments",
    "get_department_by_id",
    "search",
    "update_department",
    "delete_department",
    "get_public_staff_in_department",
    "get_all_staff_in_department",
]

router = APIRouter(
    prefix="/department",
    tags=["departments"],
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
    dependencies=[Depends(RequiresPermission("department:create"))],
    responses={
        status.HTTP_201_CREATED: {
            "model": CreateDepartmentResponse,
            "description": "Department created successfully.",
        },
        status.HTTP_409_CONFLICT: {
            "model": DepartmentAlreadyExistsExceptionResponse,
            "description": "Department with the given detail already exists.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": Union[
                StaffNotFoundExceptionResponse, SchoolNotFoundExceptionResponse
            ],
            "description": "Staff or School not found.",
        },
    },
)
async def create_department(
    body: Annotated[CreateDepartmentRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        department_id = await DepartmentRepository.create(
            connection,
            name=body.name,
            school_id=body.school_id,
            head_id=body.head_id,
            extra_info=body.extra_info,
        )
        response.status_code = status.HTTP_201_CREATED
        return CreateDepartmentResponse(id=department_id)
    except DepartmentAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return DepartmentAlreadyExistsExceptionResponse(context=e.context)
    except StaffNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StaffNotFoundExceptionResponse(context=e.context)
    except SchoolNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return SchoolNotFoundExceptionResponse(context=e.context)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListDepartmentResponse,
            "description": "List of departments",
        },
    },
)
async def get_departments(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
    school_id: Annotated[Optional[UUID], Query()] = None,
    offset: Annotated[Optional[int], Query()] = 0,
    limit: Annotated[Optional[int], Query()] = 100,
):
    if school_id:
        records = await DepartmentRepository.get_by_school_id(
            connection, school_id, limit, offset
        )
    else:
        records = await DepartmentRepository.get_all(connection, limit, offset)
    response.status_code = status.HTTP_200_OK
    return ListDepartmentResponse(
        departments=[
            Department(
                id=record["id"],
                name=record["name"],
                school_id=record["school_id"],
                head_id=record["head_id"],
                extra_info=record["extra_info"],
            )
            for record in records
        ]
    )


@router.get(
    "/search",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListDepartmentResponse,
            "description": "Department details retrieved successfully.",
        },
    },
)
async def search(
    name: Annotated[str, Query()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    records = await DepartmentRepository.get_by_name(connection, name)
    response.status_code = status.HTTP_200_OK
    return ListDepartmentResponse(
        departments=[
            Department(
                id=record["id"],
                name=record["name"],
                school_id=record["school_id"],
                head_id=record["head_id"],
                extra_info=record["extra_info"],
            )
            for record in records
        ]
    )


@router.get(
    "/{department_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": Department,
            "description": "Department details retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": DepartmentNotFoundExceptionResponse,
            "description": "Department not found.",
        },
    },
)
async def get_department_by_id(
    department_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        record = await DepartmentRepository.get_by_id(connection, department_id)
        response.status_code = status.HTTP_200_OK
        return Department(
            id=record["id"],
            name=record["name"],
            school_id=record["school_id"],
            head_id=record["head_id"],
            extra_info=record["extra_info"],
        )
    except DepartmentNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return DepartmentNotFoundExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )


@router.patch(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Department updated successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": Union[
                DepartmentNotFoundExceptionResponse,
                SchoolNotFoundExceptionResponse,
                StaffNotFoundExceptionResponse,
            ],
            "description": "Department, School, or Staff not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": DepartmentAlreadyExistsExceptionResponse,
            "description": "Department with the given detail already exists.",
        },
    },
)
async def update_department(
    department_id: Annotated[UUID, Path()],
    body: Annotated[UpdateDepartmentRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permission: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(
                ["department:update:any"], ["department:update:self"]
            )
        ),
    ],
    response: Response,
):
    try:
        if "department:update:self" in permission:
            department = await DepartmentRepository.get_by_id(connection, department_id)
            if session.user.user_id != department["head_id"]:
                response.status_code = status.HTTP_403_FORBIDDEN
                raise NotEnoughPermissionsException(context={})
        await DepartmentRepository.update(
            connection,
            department_id,
            name=body.name,
            school_id=body.school_id,
            head_id=body.head_id,
            extra_info=body.extra_info,
        )
        response.status_code = status.HTTP_204_NO_CONTENT
    except DepartmentNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return DepartmentNotFoundExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )
    except DepartmentAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return DepartmentAlreadyExistsExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )
    except SchoolNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return SchoolNotFoundExceptionResponse(context=e.context)
    except StaffNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StaffNotFoundExceptionResponse(context=e.context)


@router.delete(
    "/{department_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Department deleted successfully.",
        },
    },
)
async def delete_department(
    department_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permission: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(
                ["department:delete:any"], ["department:delete:self"]
            )
        ),
    ],
    response: Response,
):
    if "department:delete:self" in permission:
        try:
            department = await DepartmentRepository.get_by_id(connection, department_id)
            if session.user.user_id != department["head_id"]:
                response.status_code = status.HTTP_403_FORBIDDEN
                raise NotEnoughPermissionsException(context={})
        except DepartmentNotFoundException:
            response.status_code = status.HTTP_204_NO_CONTENT
            return
    await DepartmentRepository.delete(connection, department_id)
    response.status_code = status.HTTP_204_NO_CONTENT


@router.get(
    "/{department_id}/staff/public",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListDepartmentResponse,
            "description": "List of public staff in the department.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": DepartmentNotFoundExceptionResponse,
            "description": "Department not found.",
        },
    },
)
async def get_public_staff_in_department(
    department_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if not await DepartmentRepository.exists(connection, department_id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return DepartmentNotFoundExceptionResponse(
            context={"parameter": "department_id"},
        )
    records = await DepartmentRepository.get_public_staff(connection, department_id)
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
    "/{department_id}/staff",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(RequiresPermission("staff:read:any"))],
    responses={
        status.HTTP_200_OK: {
            "model": ListStaffResponse,
            "description": "List of staff in the department.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": DepartmentNotFoundExceptionResponse,
            "description": "Department not found.",
        },
    },
)
async def get_all_staff_in_department(
    department_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if not await DepartmentRepository.exists(connection, department_id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return DepartmentNotFoundExceptionResponse(
            context={"parameter": "department_id"},
        )
    records = await DepartmentRepository.get_staff(connection, department_id)
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
