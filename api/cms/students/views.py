from typing import Annotated
from uuid import UUID
from cms.auth.exceptions import NotEnoughPermissions
from fastapi import APIRouter, Body, Depends, Response, status
from cms.auth.schemas import CredentialsNotFoundResponse, NotAuthorizedResponse
from cms.students.exceptions import StudentAlreadyExists, StudentDoesNotExists
from cms.users.exceptions import UserDoesNotExists
from cms.users.schemas import UserDoesNotExistsResponse
from cms.students.schemas import (
    CreateStudentRequest,
    GetStudentResponse,
    UpdateStudentRequest,
    StudentAlreadyExistsResponse,
    StudentDoesNotExistsResponse,
)
from cms.students.repository import StudentRepository
from cms.utils.postgres import PgPool
from cms.auth.dependency import PermissionRequired, get_user_id
from asyncpg import Connection, Path

router = APIRouter(
    prefix="/students",
    tags=["students"],
    responses={
        401: {"model": CredentialsNotFoundResponse},
        403: {"model": NotAuthorizedResponse},
    },
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionRequired(["student:create:any"]))],
    responses={
        201: {"model": None},
        404: {"model": UserDoesNotExistsResponse},
        409: {"model": StudentAlreadyExistsResponse},
    },
)
async def create_student(
    student: Annotated[CreateStudentRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await StudentRepository.create(
            connection,
            student.user_id,
            student.first_name,
            student.last_name,
            student.gender,
            student.aadhaar_no,
            student.apaar_id,
        )
    except UserDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserDoesNotExistsResponse(context=e.context)
    except StudentAlreadyExists as e:
        response.status_code = status.HTTP_409_CONFLICT
        return StudentAlreadyExistsResponse(context=e.context)

@router.get(
    "/",
    dependencies=[Depends(PermissionRequired(["student:read:any"]))],
    responses={
        200: {"model": list[GetStudentResponse]},
    },
)
async def get_students(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    result = await StudentRepository.get_all(connection)
    response.status_code = status.HTTP_200_OK
    return [
        GetStudentResponse(
            id=record["id"],
            first_name=record["first_name"],
            last_name=record["last_name"],
            gender=record["gender"],
            aadhaar_no=record["aadhaar_no"],
            apaar_id=record["apaar_id"],
            active=record["active"]
        ) for record in result
    ]

@router.get(
    "/{id}",
    responses={
        200: {"model": GetStudentResponse},
        404: {"model": StudentDoesNotExistsResponse},
    },
)
async def get_student(
    id: Annotated[UUID, Path()],
    user_permission: Annotated[
        list[str],
        Depends(PermissionRequired(["student:read:any"], ["student:read:self"])),
    ],
    user_id: Annotated[UUID, Depends(get_user_id)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if "student:read:self" in user_permission and id != user_id:
        raise NotEnoughPermissions()
    try:
        result = await StudentRepository.get_by_id(connection, id)
        response.status_code = status.HTTP_200_OK
        return GetStudentResponse(
            id=result["id"],
            first_name=result["first_name"],
            last_name=result["last_name"],
            gender=result["gender"],
            aadhaar_no=result["aadhaar_no"],
            apaar_id=result["apaar_id"],
            active=result["active"],
        )
    except StudentDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentDoesNotExistsResponse(context=e.context)


@router.patch(
    "/{id}",
    responses={
        200: {"model": None},
        404: {"model": StudentDoesNotExistsResponse},
    },
)
async def update_student(
    id: Annotated[UUID, Path()],
    student: Annotated[UpdateStudentRequest, Body()],
    user_permission: Annotated[
        list[str],
        Depends(PermissionRequired(["student:update:any"], ["student:update:self"])),
    ],
    user_id: Annotated[UUID, Depends(get_user_id)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if "student:update:self" in user_permission and id != user_id:
        raise NotEnoughPermissions()
    try:
        await StudentRepository.update(
            connection,
            id,
            student.first_name,
            student.last_name,
            student.gender,
            student.aadhaar_no,
            student.apaar_id,
        )
        response.status_code = status.HTTP_200_OK
        return
    except StudentDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentDoesNotExistsResponse(context=e.context)


@router.delete(
    "/{id}",
    dependencies=[Depends(PermissionRequired(["student:delete:any"]))],
    responses={
        200: {"model": None},
        404: {"model": StudentDoesNotExistsResponse},
    },
)
async def delete_student(
    id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await StudentRepository.delete(connection, id)
        response.status_code = status.HTTP_200_OK
        return
    except StudentDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentDoesNotExistsResponse(context=e.context)
