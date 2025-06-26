from typing import Annotated, Optional
from uuid import UUID

from asyncpg import Connection
from cms.auth.dependency import (
    RequiresAnyOfGivenPermission,
    RequiresPermission,
    get_session,
)
from cms.auth.exceptions import NotEnoughPermissionsException

# filepath: /workspaces/cms/api/cms/schools/views.py
from cms.auth.models import (
    CredentialsNotFoundExceptionResponse,
    NotAuthorizedExceptionResponse,
    Session,
)
from cms.schools.exceptions import SchoolAlreadyExistsException, SchoolNotFoundException
from cms.schools.models import (
    CreateSchoolRequest,
    CreateSchoolResponse,
    ListSchoolResponse,
    School,
    SchoolAlreadyExistsExceptionResponse,
    SchoolNotFoundExceptionResponse,
    UpdateSchoolRequest,
)
from cms.schools.repository import SchoolRepository
from cms.staff.exceptions import StaffNotFoundException
from cms.staff.models import StaffNotFoundExceptionResponse
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Path, Query, Response, status

__all__ = [
    "router",
    "create_school",
    "get_all_schools",
    "get_school_by_id",
    "search_school_by_name",
    "update_school",
    "delete_school",
]

router = APIRouter(
    prefix="/school",
    tags=["schools"],
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
    dependencies=[Depends(RequiresPermission("school:create"))],
    responses={
        status.HTTP_201_CREATED: {
            "model": CreateSchoolResponse,
            "description": "School created successfully.",
        },
        status.HTTP_409_CONFLICT: {
            "model": SchoolAlreadyExistsExceptionResponse,
            "description": "School with the given detail already exists.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": StaffNotFoundExceptionResponse,
            "description": "Dean not found.",
        },
    },
)
async def create_school(
    body: Annotated[CreateSchoolRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        school_id = await SchoolRepository.create(
            connection,
            name=body.name,
            dean_id=body.dean_id,
            extra_info=body.extra_info,
        )
        response.status_code = status.HTTP_201_CREATED
        return CreateSchoolResponse(school_id=school_id)
    except SchoolAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return SchoolAlreadyExistsExceptionResponse(context=e.context)
    except StaffNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StaffNotFoundExceptionResponse(context=e.context)


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListSchoolResponse,
            "description": "List of schools",
        },
    },
)
async def get_all_schools(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
    offset: Annotated[Optional[int], Query()] = 0,
    limit: Annotated[Optional[int], Query()] = 100,
):
    records = await SchoolRepository.get_all(connection, limit, offset)
    response.status_code = status.HTTP_200_OK
    return ListSchoolResponse(
        schools=[
            School(
                school_id=record["id"],
                name=record["name"],
                dean_id=record["dean_id"],
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
            "model": ListSchoolResponse,
            "description": "School details retrieved successfully by name.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": SchoolNotFoundExceptionResponse,
            "description": "School not found by name.",
        },
    },
)
async def search_school_by_name(
    name: Annotated[str, Query()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        records = await SchoolRepository.get_by_name(connection, name)
        response.status_code = status.HTTP_200_OK
        return ListSchoolResponse(
            schools=[
                School(
                    school_id=record["id"],
                    name=record["name"],
                    dean_id=record["dean_id"],
                    extra_info=record["extra_info"],
                )
                for record in records
            ]
        )
    except SchoolNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return SchoolNotFoundExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )


@router.get(
    "/{school_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": School,
            "description": "School details retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": SchoolNotFoundExceptionResponse,
            "description": "School not found.",
        },
    },
)
async def get_school_by_id(
    school_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        record = await SchoolRepository.get_by_id(connection, school_id)
        response.status_code = status.HTTP_200_OK
        return School(
            school_id=record["id"],
            name=record["name"],
            dean_id=record["dean_id"],
            extra_info=record["extra_info"],
        )
    except SchoolNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return SchoolNotFoundExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )


@router.patch(
    "/{school_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "School updated successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": SchoolNotFoundExceptionResponse,
            "description": "School not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": SchoolAlreadyExistsExceptionResponse,
            "description": "School with the given detail already exists.",
        },
    },
)
async def update_school(
    school_id: Annotated[UUID, Path()],
    body: Annotated[UpdateSchoolRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permission: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(["school:update:any"], ["school:update:self"])
        ),
    ],
    response: Response,
):
    try:
        if "school:update:self" in permission:
            school = await SchoolRepository.get_by_id(connection, school_id)
            if session.user.user_id != school["dean_id"]:
                response.status_code = status.HTTP_403_FORBIDDEN
                raise NotEnoughPermissionsException(context={})
        await SchoolRepository.update(
            connection,
            school_id,
            name=body.name,
            dean_id=body.dean_id,
            extra_info=body.extra_info,
        )
        response.status_code = status.HTTP_204_NO_CONTENT
    except SchoolNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return SchoolNotFoundExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )
    except SchoolAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return SchoolAlreadyExistsExceptionResponse(
            slug=e.slug, description=e.description, context=e.context
        )


@router.delete(
    "/{school_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "School deleted successfully.",
        },
    },
)
async def delete_school(
    school_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permission: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(["school:delete:any"], ["school:delete:self"])
        ),
    ],
    response: Response,
):
    if "school:delete:self" in permission:
        try:
            school = await SchoolRepository.get_by_id(connection, school_id)
            if session.user.user_id != school["dean_id"]:
                response.status_code = status.HTTP_403_FORBIDDEN
                raise NotEnoughPermissionsException(context={})
        except SchoolNotFoundException:
            response.status_code = status.HTTP_204_NO_CONTENT
            return
    await SchoolRepository.delete(connection, school_id)
    response.status_code = status.HTTP_204_NO_CONTENT
