from typing import Annotated, Optional
from uuid import UUID
from asyncpg import Connection
from cms.auth.exceptions import NotEnoughPermissionsException
from cms.parents.repository import ParentRepository
from cms.students.models import Student
from cms.students.views import ListStudentResponse
from cms.users.exceptions import UserAlreadyExistsException
from cms.users.repository import UserRepository
from cms.utils.argon2 import hash_password
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Path, Query, Response, status

from cms.auth.dependency import (
    RequiresAnyOfGivenPermission,
    RequiresPermission,
    get_session,
)
from cms.auth.models import (
    CredentialsNotFoundExceptionResponse,
    NotAuthorizedExceptionResponse,
    Session,
)
from cms.parents.exceptions import (
    ParentAlreadyExistsException,
    ParentNotFoundException,
)
from cms.parents.models import (
    CreateParentRequest,
    CreateParentResponse,
    ListParentResponse,
    Parent,
    ParentAlreadyExistsExceptionResponse,
    ParentNotFoundExceptionResponse,
    UpdateParentRequest,
)

__all__ = [
    "router",
    "create_parent",
    "get_all_parents",
    "get_parent_by_id",
    "update_parent",
    "delete_parent",
]

router = APIRouter(
    prefix="/parent",
    tags=["parents"],
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
    dependencies=[Depends(RequiresPermission("parent:create"))],
    responses={
        status.HTTP_201_CREATED: {
            "model": CreateParentResponse,
            "description": "Parent created successfully.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ParentAlreadyExistsExceptionResponse,
            "description": "Parent with the given detail already exists.",
        },
    },
)
async def create_parent(
    body: Annotated[CreateParentRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    async with connection.transaction():
        try:
            async with connection.transaction():
                user_id = await UserRepository.create(
                    connection,
                    body.fathers_email_id,
                    hash_password("Parent@123"),
                    body.fathers_contact_no,
                )
        except UserAlreadyExistsException as e:
            if e.context["parameter"] == "email_id":
                user = await UserRepository.get_by_email_id(
                    connection, body.fathers_email_id
                )
            elif e.context["parameter"] == "contact_no":
                user = await UserRepository.get_by_contact_no(
                    connection, body.fathers_contact_no
                )
            else:
                raise e
            user_id = user["id"]

        try:
            # Create the parent record
            parent_id = await ParentRepository.create(
                connection,
                user_id=user_id,
                fathers_name=body.fathers_name,
                mothers_name=body.mothers_name,
                fathers_email_id=body.fathers_email_id,
                mothers_email_id=body.mothers_email_id,
                fathers_contact_no=str(body.fathers_contact_no),
                mothers_contact_no=str(body.mothers_contact_no),
                address=body.address,
                extra_info=body.extra_info,
            )
            response.status_code = status.HTTP_201_CREATED
            return CreateParentResponse(parent_id=parent_id)
        except ParentAlreadyExistsException as e:
            response.status_code = status.HTTP_409_CONFLICT
            return ParentAlreadyExistsExceptionResponse(context=e.context)


@router.get(
    "/",
    dependencies=[Depends(RequiresPermission("parent:read:any"))],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListParentResponse,
            "description": "List of parents",
        },
    },
)
async def get_all_parents(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
    offset: Annotated[Optional[int], Query()] = 0,
    limit: Annotated[Optional[int], Query()] = 100,
):
    records = await ParentRepository.get_all(connection, limit, offset)
    response.status_code = status.HTTP_200_OK
    return ListParentResponse(
        parents=[
            Parent(
                id=record["id"],
                fathers_name=record["fathers_name"],
                mothers_name=record["mothers_name"],
                fathers_email_id=record["fathers_email_id"],
                mothers_email_id=record["mothers_email_id"],
                fathers_contact_no=record["fathers_contact_no"],
                mothers_contact_no=record["mothers_contact_no"],
                address=record["address"],
                extra_info=record["extra_info"],
            )
            for record in records
        ]
    )


@router.get(
    "/{parent_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": Parent,
            "description": "Parent details retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ParentNotFoundExceptionResponse,
            "description": "Parent not found.",
        },
    },
)
async def get_parent_by_id(
    parent_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(["parent:read:any"], ["parent:read:self"])
        ),
    ],
    response: Response,
):
    # Check if parent is accessing their own data or has permission to read any parent
    if "parent:read:self" in permissions and parent_id != session.user.user_id:
        raise NotEnoughPermissionsException()

    try:
        record = await ParentRepository.get_by_id(connection, parent_id)
        response.status_code = status.HTTP_200_OK
        return Parent(
            id=record["id"],
            fathers_name=record["fathers_name"],
            mothers_name=record["mothers_name"],
            fathers_email_id=record["fathers_email_id"],
            mothers_email_id=record["mothers_email_id"],
            fathers_contact_no=record["fathers_contact_no"],
            mothers_contact_no=record["mothers_contact_no"],
            address=record["address"],
            extra_info=record["extra_info"],
        )
    except ParentNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ParentNotFoundExceptionResponse(context=e.context)


@router.patch(
    "/{parent_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Parent updated successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ParentNotFoundExceptionResponse,
            "description": "Parent not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": ParentAlreadyExistsExceptionResponse,
            "description": "Parent with the given detail already exists.",
        },
    },
)
async def update_parent(
    parent_id: Annotated[UUID, Path()],
    body: Annotated[UpdateParentRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(["parent:update:any"], ["parent:update:self"])
        ),
    ],
    response: Response,
):
    # Check if parent is updating their own data or has permission to update any parent
    if "parent:update:self" in permissions and parent_id != session.user.user_id:
        raise NotEnoughPermissionsException()

    try:
        await ParentRepository.update(
            connection,
            parent_id,
            fathers_name=body.fathers_name,
            mothers_name=body.mothers_name,
            fathers_email_id=body.fathers_email_id,
            mothers_email_id=body.mothers_email_id,
            fathers_contact_no=str(body.fathers_contact_no)
            if body.fathers_contact_no
            else None,
            mothers_contact_no=str(body.mothers_contact_no)
            if body.mothers_contact_no
            else None,
            address=body.address,
            extra_info=body.extra_info,
        )
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    except ParentNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ParentNotFoundExceptionResponse(context=e.context)
    except ParentAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return ParentAlreadyExistsExceptionResponse(context=e.context)


@router.delete(
    "/{parent_id}",
    dependencies=[Depends(RequiresPermission("parent:delete"))],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Parent deleted successfully.",
        },
    },
)
async def delete_parent(
    parent_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    await ParentRepository.delete(connection, parent_id)
    response.status_code = status.HTTP_204_NO_CONTENT
    return


@router.get(
    "/{parent_id}/students",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListStudentResponse,
            "description": "List of students associated with the parent.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": ParentNotFoundExceptionResponse,
            "description": "Parent not found.",
        },
    },
)
async def get_students(
    parent_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(["student:read:any"], ["student:read:self"])
        ),
    ],
    response: Response,
):
    # Check if parent is accessing their own data or has permission to read any student
    if "student:read:self" in permissions and parent_id != session.user.user_id:
        raise NotEnoughPermissionsException()
    if not await ParentRepository.exists(connection, parent_id):
        return ParentNotFoundExceptionResponse(context={"parameter": "parent_id"})

    records = await ParentRepository.get_students(connection, parent_id)
    response.status_code = status.HTTP_200_OK
    return ListStudentResponse(
        students=[
            Student(
                id=record["id"],
                first_name=record["first_name"],
                middle_name=record["middle_name"],
                last_name=record["last_name"],
                date_of_birth=record["date_of_birth"],
                gender=record["gender"],
                address=record["address"],
                email_id=record["email_id"],
                contact_no=record["contact_no"],
                aadhaar_no=record["aadhaar_no"],
                apaar_id=record["apaar_id"],
                extra_info=record["extra_info"],
            )
            for record in records
        ]
    )
