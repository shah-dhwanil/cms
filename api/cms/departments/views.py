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
from cms.staff.models import StaffNotFoundExceptionResponse
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Path, Query, Response, status

__all__ = [
    "router",
    "create_department",
    "get_all_departments",
    "get_department_by_id",
    "search_department_by_name",
    "get_departments_by_school_id",
    "update_department",
    "delete_department",
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
async def get_all_departments(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
    offset: Annotated[Optional[int], Query()] = 0,
    limit: Annotated[Optional[int], Query()] = 100,
):
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


@router.get(
    "/search_by_name/{name}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListDepartmentResponse,
            "description": "Department details retrieved successfully by name.",
        },
    },
)
async def search_department_by_name(
    name: Annotated[str, Path()],
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
    "/school/{school_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListDepartmentResponse,
            "description": "List of departments in a school.",
        },
    },
)
async def get_departments_by_school_id(
    school_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
    offset: Annotated[Optional[int], Query()] = 0,
    limit: Annotated[Optional[int], Query()] = 100,
):
    records = await DepartmentRepository.get_by_school_id(
        connection, school_id, limit, offset
    )
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
