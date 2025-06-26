from typing import Annotated, Union
from uuid import UUID

from asyncpg import Connection
from cms.auth.dependency import (
    RequiresPermission,
)
from cms.auth.models import (
    CredentialsNotFoundExceptionResponse,
    NotAuthorizedExceptionResponse,
)
from cms.departments.exceptions import DepartmentNotFoundException
from cms.departments.models import DepartmentNotFoundExceptionResponse
from cms.programs.exceptions import (
    ProgramAlreadyExistsException,
    ProgramNotFoundException,
)
from cms.programs.models import (
    CreateProgramRequest,
    CreateProgramResponse,
    GetProgramRequest,
    ListProgramResponse,
    Program,
    ProgramAlreadyExistsExceptionResponse,
    ProgramNotFoundExceptionResponse,
    UpdateProgramRequest,
)
from cms.programs.repository import ProgramRepository
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Path, Query, Response, status

__all__ = [
    "router",
    "create_program",
    "get_programs",
    "get_program_by_id",
    "search_program",
    "update_program",
    "delete_program",
]

router = APIRouter(
    prefix="/program",
    tags=["programs"],
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
    dependencies=[Depends(RequiresPermission("program:create"))],
    responses={
        status.HTTP_201_CREATED: {
            "model": CreateProgramResponse,
            "description": "Program created successfully.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ProgramAlreadyExistsExceptionResponse,
            "description": "Program with the given detail already exists.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": DepartmentNotFoundExceptionResponse,
            "description": "Department not found.",
        },
    },
)
async def create_program(
    body: Annotated[CreateProgramRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        program_id = await ProgramRepository.create(
            connection,
            name=body.name,
            degree_name=body.degree_name,
            degree_type=body.degree_type,
            offered_by=body.offered_by,
            extra_info=body.extra_info,
        )
        response.status_code = status.HTTP_201_CREATED
        return CreateProgramResponse(id=program_id)
    except ProgramAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return ProgramAlreadyExistsExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )
    except DepartmentNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return DepartmentNotFoundExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListProgramResponse,
            "description": "List of programs in a school.",
        },
    },
)
async def get_programs(
    query: Annotated[GetProgramRequest, Query()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if query.department_id:
        records = await ProgramRepository.get_by_department(
            connection, query.department_id, query.limit, query.offset
        )
    elif query.school_id:
        records = await ProgramRepository.get_by_school(
            connection, query.school_id, query.limit, query.offset
        )
    else:
        records = await ProgramRepository.get_all(connection, query.limit, query.offset)
    response.status_code = status.HTTP_200_OK
    return ListProgramResponse(
        programs=[
            Program(
                id=record["id"],
                name=record["name"],
                degree_name=record["degree_name"],
                degree_type=record["degree_type"],
                department_id=record["department_id"],
                department_name=record["department_name"],
                extra_info=record["extra_info"],
            )
            for record in records
        ]
    )


@router.get(
    "/{program_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": Program,
            "description": "Program details retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ProgramNotFoundExceptionResponse,
            "description": "Program not found.",
        },
    },
)
async def get_program_by_id(
    program_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        record = await ProgramRepository.get_by_id(connection, program_id)
        response.status_code = status.HTTP_200_OK
        return Program(
            id=record["id"],
            name=record["name"],
            degree_name=record["degree_name"],
            degree_type=record["degree_type"],
            department_id=record["department_id"],
            department_name=record["department_name"],
            extra_info=record["extra_info"],
        )
    except ProgramNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ProgramNotFoundExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )


@router.get(
    "/search",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListProgramResponse,
            "description": "Program details retrieved successfully by name.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ProgramNotFoundExceptionResponse,
            "description": "Program not found.",
        },
    },
)
async def search_program(
    name: Annotated[str, Query()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    records = await ProgramRepository.search_by_name(connection, name)
    response.status_code = status.HTTP_200_OK
    return ListProgramResponse(
        programs=[
            Program(
                id=record["id"],
                name=record["name"],
                degree_name=record["degree_name"],
                degree_type=record["degree_type"],
                department_id=record["department_id"],
                department_name=record["department_name"],
                extra_info=record["extra_info"],
            )
            for record in records
        ]
    )


@router.patch(
    "/{program_id}",
    dependencies=[Depends(RequiresPermission("program:update"))],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Program updated successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": Union[
                ProgramNotFoundExceptionResponse,
                DepartmentNotFoundExceptionResponse,
            ],
            "description": "Program or Department not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ProgramAlreadyExistsExceptionResponse,
            "description": "Program with the given detail already exists.",
        },
    },
)
async def update_program(
    program_id: Annotated[UUID, Path()],
    body: Annotated[UpdateProgramRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await ProgramRepository.update(
            connection,
            program_id,
            name=body.name,
            degree_name=body.degree_name,
            degree_type=body.degree_type,
            offered_by=body.offered_by,
            extra_info=body.extra_info,
        )
        response.status_code = status.HTTP_204_NO_CONTENT
    except ProgramNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ProgramNotFoundExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )
    except ProgramAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return ProgramAlreadyExistsExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )
    except DepartmentNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return DepartmentNotFoundExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )


@router.delete(
    "/{program_id}",
    dependencies=[Depends(RequiresPermission("program:delete"))],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Program deleted successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ProgramNotFoundExceptionResponse,
            "description": "Program not found.",
        },
    },
)
async def delete_program(
    program_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await ProgramRepository.delete(connection, program_id)
        response.status_code = status.HTTP_204_NO_CONTENT
    except ProgramNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ProgramNotFoundExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )
