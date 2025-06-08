from typing import Annotated, Union
from uuid import UUID
from asyncpg import Connection, Path
from cms.auth.exceptions import NotEnoughPermissions
from cms.students.exceptions import StudentAlreadyExists, StudentDoesNotExists
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Response, status
from cms.parents.exceptions import ParentAlreadyExists, ParentDoesNotExists
from cms.parents.schemas import (
    CreateParentRequest,
    GetParentResponse,
    UpdateParentRequest,
    ParentAlreadyExistsResponse,
    ParentDoesNotExistsResponse,
    GetStudentResponse,
)
from cms.parents.repository import ParentRepository
from cms.users.exceptions import UserDoesNotExists
from cms.users.schemas import UserDoesNotExistsResponse
from cms.students.schemas import (
    StudentAlreadyExistsResponse,
    StudentDoesNotExistsResponse,
)
from cms.auth.schemas import CredentialsNotFoundResponse, NotAuthorizedResponse
from cms.auth.dependency import PermissionRequired, get_user_id

router = APIRouter(
    prefix="/parents",
    tags=["parents"],
    responses={
        401: {"model": CredentialsNotFoundResponse},
        403: {"model": NotAuthorizedResponse},
    },
)


@router.post(
    "/",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(PermissionRequired(["parents:create:any"]))],
    responses={
        409: {"model": ParentAlreadyExistsResponse},
        404: {"model": UserDoesNotExistsResponse},
    },
)
async def create_parent(
    parent: Annotated[CreateParentRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await ParentRepository.create(
            connection,
            parent.user_id,
            parent.father_name,
            parent.mother_name,
            parent.address,
        )
        response.status_code = status.HTTP_201_CREATED
        return
    except ParentAlreadyExists as e:
        response.status_code = status.HTTP_409_CONFLICT
        return ParentAlreadyExistsResponse(context=e.context)
    except UserDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return UserDoesNotExistsResponse(context=e.context)


@router.get(
    "/{id}",
    responses={
        200: {"model": GetParentResponse},
        404: {"model": ParentDoesNotExistsResponse},
    },
)
async def get_parent(
    id: Annotated[UUID, Path()],
    user_permissions: Annotated[
        list[str],
        Depends(PermissionRequired(["parents:read:any"], ["parents:read:self"])),
    ],
    user_id: Annotated[UUID, Depends(get_user_id)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if "parents:read:self" in user_permissions and user_id != id:
        raise NotEnoughPermissions()
    try:
        parent = await ParentRepository.get_by_id(connection, id)
        response.status_code = status.HTTP_200_OK
        return GetParentResponse(
            user_id=parent["id"],
            father_name=parent["father_name"],
            mother_name=parent["mother_name"],
            address=parent["address"],
            active=parent["active"],
        )
    except ParentDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ParentDoesNotExistsResponse(context=e.context)


@router.patch(
    "/{id}",
    dependencies=[Depends(PermissionRequired(["parents:update:self"]))],
    responses={200: {"model": None}, 404: {"model": ParentDoesNotExistsResponse}},
)
async def update_parent(
    parent: Annotated[UpdateParentRequest, Body()],
    id: UUID,
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await ParentRepository.update(
            connection, id, parent.father_name, parent.mother_name, parent.address
        )
        response.status_code = status.HTTP_200_OK
        return
    except ParentDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ParentDoesNotExistsResponse(context=e.context)


@router.delete(
    "/{id}",
    dependencies=[Depends(PermissionRequired(["parents:delete:any"]))],
    responses={200: {"model": None}, 404: {"model": ParentDoesNotExistsResponse}},
)
async def delete_parent(
    id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await ParentRepository.delete(connection, id)
        response.status_code = status.HTTP_200_OK
        return
    except ParentDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ParentDoesNotExistsResponse(context=e.context)


@router.post(
    "/{parent_id}/link/{student_id}",
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(PermissionRequired(["parents:create:any", "student:create:any"]))
    ],
    responses={
        409: {"model": StudentAlreadyExistsResponse},
        404: {
            "model": Union[ParentDoesNotExistsResponse, StudentDoesNotExistsResponse]
        },
    },
)
async def link_student(
    parent_id: Annotated[UUID, Path()],
    student_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await ParentRepository.link_student(connection, student_id, parent_id)
        response.status_code = status.HTTP_201_CREATED
        return
    except ParentDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ParentDoesNotExistsResponse(context=e.context)
    except StudentDoesNotExists as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentDoesNotExistsResponse(context=e.context)
    except StudentAlreadyExists as e:
        response.status_code = status.HTTP_409_CONFLICT
        return StudentAlreadyExistsResponse(context=e.context)


@router.post(
    "/{parent_id}/unlink/{student_id}",
    dependencies=[
        Depends(PermissionRequired(["parents:delete:any", "student:delete:any"]))
    ],
    responses={200: {"model": None}, 404: {"model": ParentDoesNotExistsResponse}},
)
async def unlink_student(
    parent_id: Annotated[UUID, Path()],
    student_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    await ParentRepository.unlink_student(connection, parent_id, student_id)
    response.status_code = status.HTTP_200_OK
    return


@router.get("/{id}/students", responses={200: {"model": list[GetStudentResponse]}})
async def get_students(
    id: Annotated[UUID, Path()],
    user_permissions: Annotated[
        list[str],
        Depends(PermissionRequired(["student:read:any"], ["student:read:self"])),
    ],
    user_id: Annotated[UUID, Depends(get_user_id)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if "students:read:self" in user_permissions and user_id != id:
        raise NotEnoughPermissions()
    students = await ParentRepository.get_students(connection, id)
    response.status_code = status.HTTP_200_OK
    return [
        GetStudentResponse(
            id=student["id"],
            first_name=student["first_name"],
            last_name=student["last_name"],
        )
        for student in students
    ]
