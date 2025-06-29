from datetime import timedelta
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
from cms.batch.exceptions import BatchNotFoundException
from cms.batch.models import BatchNotFoundExceptionResponse
from cms.parents.exceptions import ParentNotFoundException
from cms.parents.models import Parent, ParentNotFoundExceptionResponse
from cms.students.exceptions import (
    StudentAlreadyExistsException,
    StudentNotFoundException,
)
from cms.students.models import (
    CreateStudentRequest,
    CreateStudentResponse,
    GetStudentAdhaarResponse,
    GetStudentApaarResponse,
    ListStudentEnrollmentResponse,
    ListStudentResponse,
    Student,
    StudentAlreadyExistsExceptionResponse,
    StudentEnrollRequest,
    StudentEnrollResponse,
    StudentNotFoundExceptionResponse,
    UpdateStudentRequest,
)
from cms.students.repository import StudentRepository
from cms.users.exceptions import UserAlreadyExistsException
from cms.users.repository import UserRepository
from cms.utils.argon2 import hash_password
from cms.utils.minio import MinioClient
from cms.utils.postgres import PgPool
from fastapi import APIRouter, Body, Depends, Path, Query, Response, UploadFile, status

__all__ = [
    "router",
    "create_student",
    "get_all_students",
    "get_student_by_id",
    "update_student",
    "delete_student",
]

router = APIRouter(
    prefix="/student",
    tags=["students"],
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
    dependencies=[Depends(RequiresPermission("student:create"))],
    responses={
        status.HTTP_201_CREATED: {
            "model": CreateStudentResponse,
            "description": "Student created successfully.",
        },
        status.HTTP_409_CONFLICT: {
            "model": StudentAlreadyExistsExceptionResponse,
            "description": "Student with the given detail already exists.",
        },
    },
)
async def create_student(
    body: Annotated[CreateStudentRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    async with connection.transaction():
        try:
            async with connection.transaction():
                user_id = await UserRepository.create(
                    connection,
                    body.email_id,
                    hash_password("Student@123"),
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
            student_id = await StudentRepository.create(
                connection,
                user_id,
                body.first_name,
                body.middle_name,
                body.last_name,
                body.date_of_birth,
                body.gender,
                body.address,
                body.aadhaar_no,
                body.apaar_id,
                body.extra_info,
            )
            response.status_code = status.HTTP_201_CREATED
            return CreateStudentResponse(student_id=student_id)
        except StudentAlreadyExistsException as e:
            response.status_code = status.HTTP_409_CONFLICT
            return StudentAlreadyExistsExceptionResponse(context=e.context)


@router.get(
    "/",
    dependencies=[Depends(RequiresPermission("student:read:any"))],
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListStudentResponse,
            "description": "List of students",
        },
    },
)
async def get_all_students(
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
    offset: Annotated[Optional[int], Query()] = 0,
    limit: Annotated[Optional[int], Query()] = 100,
):
    records = await StudentRepository.get_all(connection, limit, offset)
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


@router.get(
    "/{student_id}",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": Student,
            "description": "Student details retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": StudentNotFoundExceptionResponse,
            "description": "Student not found.",
        },
    },
)
async def get_student_by_id(
    student_id: Annotated[UUID, Path()],
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
    # Check if student is accessing their own data or has permission to read any student
    if "student:read:self" in permissions and student_id != session.user.user_id:
        raise NotEnoughPermissionsException()

    try:
        record = await StudentRepository.get_by_id(connection, student_id)
        response.status_code = status.HTTP_200_OK
        return Student(
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
    except StudentNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentNotFoundExceptionResponse(context=e.context)


@router.patch(
    "/{student_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Student updated successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": StudentNotFoundExceptionResponse,
            "description": "Student not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": StudentAlreadyExistsExceptionResponse,
            "description": "Student with the given detail already exists.",
        },
    },
)
async def update_student(
    student_id: Annotated[UUID, Path()],
    body: Annotated[UpdateStudentRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(
                ["student:update:any"], ["student:update:self"]
            )
        ),
    ],
    response: Response,
):
    # Check if student is updating their own data or has permission to update any student
    if "student:update:self" in permissions and student_id != session.user.user_id:
        raise NotEnoughPermissionsException()

    try:
        await StudentRepository.update(
            connection,
            student_id,
            body.first_name,
            body.midlle_name,
            body.last_name,
            body.date_of_birth,
            body.gender,
            body.address,
            body.aadhaar_no,
            body.apaar_id,
            body.extra_info,
        )
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    except StudentNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentNotFoundExceptionResponse(context=e.context)
    except StudentAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return StudentAlreadyExistsExceptionResponse(context=e.context)


@router.delete(
    "/{student_id}",
    dependencies=[Depends(RequiresPermission("student:delete"))],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Student deleted successfully.",
        },
    },
)
async def delete_student(
    student_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    await StudentRepository.delete(connection, student_id)
    response.status_code = status.HTTP_204_NO_CONTENT
    return


@router.post(
    "/{student_id}/addhar_card",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Aadhaar card uploaded successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": StudentNotFoundExceptionResponse,
            "description": "Student not found.",
        },
    },
)
async def upload_aadhaar_card(
    student_id: Annotated[UUID, Path()],
    file: UploadFile,
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(
                ["student:create"], ["student:update:any"], ["student:update:self"]
            )
        ),
    ],
    response: Response,
):
    # Check if student is updating their own data or has permission to update any student
    if "student:update:self" in permissions and student_id != session.user.user_id:
        raise NotEnoughPermissionsException()
    if not StudentRepository.exists(connection, student_id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentNotFoundExceptionResponse(context={"parameter": "student_id"})
    async with MinioClient.get_client() as client:
        await client.put_object(
            bucket_name="aadhaar",
            object_name=str(student_id),
            data=file,
            length=file.size,
            content_type=file.content_type,
            metadata={
                "file_name": file.filename,
            },
        )
    response.status_code = status.HTTP_204_NO_CONTENT
    return


@router.post(
    "/{student_id}/apaar_id",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Apaar ID uploaded successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": StudentNotFoundExceptionResponse,
            "description": "Student not found.",
        },
    },
)
async def upload_apaar_id(
    student_id: Annotated[UUID, Path()],
    file: UploadFile,
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(
                ["student:create"], ["student:update:any"], ["student:update:self"]
            )
        ),
    ],
    response: Response,
):
    # Check if student is updating their own data or has permission to update any student
    if "student:update:self" in permissions and student_id != session.user.user_id:
        raise NotEnoughPermissionsException()
    if not StudentRepository.exists(connection, student_id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentNotFoundExceptionResponse(context={"parameter": "student_id"})
    async with MinioClient.get_client() as client:
        await client.put_object(
            bucket_name="apaar",
            object_name=str(student_id),
            data=file,
            length=file.size,
            content_type=file.content_type,
            metadata={
                "file_name": file.filename,
            },
        )
    response.status_code = status.HTTP_204_NO_CONTENT
    return


@router.get(
    "/{student_id}/aadhaar_card",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": GetStudentAdhaarResponse,
            "description": "Aadhaar card URL retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": StudentNotFoundExceptionResponse,
            "description": "Student not found.",
        },
    },
)
async def get_aadhaar_card(
    student_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(
                ["student:aadhaar:download"], ["student:read:self"]
            )
        ),
    ],
    response: Response,
):
    # Check if student is accessing their own data or has permission to read any student
    if "student:read:self" in permissions and student_id != session.user.user_id:
        raise NotEnoughPermissionsException()

    if not StudentRepository.exists(connection, student_id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentNotFoundExceptionResponse(context={"parameter": "student_id"})

    async with MinioClient.get_client() as client:
        url = await client.get_presigned_url(
            method="GET",
            bucket_name="aadhaar",
            object_name=str(student_id),
            expires=timedelta(minutes=10),  # URL valid for 10 min
        )

    response.status_code = status.HTTP_200_OK
    return GetStudentAdhaarResponse(url=url)


@router.get(
    "/{student_id}/apaar_id",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": GetStudentApaarResponse,
            "description": "Apaar ID URL retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": StudentNotFoundExceptionResponse,
            "description": "Student not found.",
        },
    },
)
async def get_apaar_id(
    student_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    session: Annotated[Session, Depends(get_session)],
    permissions: Annotated[
        list[str],
        Depends(
            RequiresAnyOfGivenPermission(
                ["student:apaar:download"], ["student:read:self"]
            )
        ),
    ],
    response: Response,
):
    # Check if student is accessing their own data or has permission to read any student
    if "student:read:self" in permissions and student_id != session.user.user_id:
        raise NotEnoughPermissionsException()

    if not StudentRepository.exists(connection, student_id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentNotFoundExceptionResponse(context={"parameter": "student_id"})

    async with MinioClient.get_client() as client:
        url = await client.get_presigned_url(
            method="GET",
            bucket_name="apaar",
            object_name=str(student_id),
            expires=timedelta(minutes=10),
        )

    response.status_code = status.HTTP_200_OK
    return GetStudentApaarResponse(url=url)


@router.post(
    "/{student_id}/parent/{parent_id}",
    dependencies=[Depends(RequiresPermission("student:link_parent"))],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Parent linked to student successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": Union[
                StudentNotFoundExceptionResponse, ParentNotFoundExceptionResponse
            ],
            "description": "Entity not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": StudentAlreadyExistsExceptionResponse,
            "description": "Student already has a parent linked.",
        },
    },
)
async def link_parent(
    student_id: Annotated[UUID, Path()],
    parent_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        await StudentRepository.set_parent(connection, student_id, parent_id)
    except StudentNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentNotFoundExceptionResponse(context=e.context)
    except ParentNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ParentNotFoundExceptionResponse(context=e.context)
    except StudentAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return StudentAlreadyExistsExceptionResponse(context=e.context)
    response.status_code = status.HTTP_204_NO_CONTENT
    return


@router.get(
    "/{student_id}/parent",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": Parent,
            "description": "Parent linked to student retrieved successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": Union[
                StudentNotFoundExceptionResponse, ParentNotFoundExceptionResponse
            ],
            "description": "Entity not found.",
        },
    },
)
async def get_parent(
    student_id: Annotated[UUID, Path()],
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
    if "parent:read:self" in permissions and student_id != session.user.user_id:
        raise NotEnoughPermissionsException()
    if not await StudentRepository.exists(connection, student_id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentNotFoundExceptionResponse(context={"parameter": "student_id"})

    record = await StudentRepository.get_parent(connection, student_id)
    if not record:
        response.status_code = status.HTTP_404_NOT_FOUND
        return ParentNotFoundExceptionResponse(context={"parameter": "parent_id"})

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


@router.delete(
    "/{student_id}/parent/{parent_id}",
    dependencies=[Depends(RequiresPermission("student:unlink_parent"))],
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Parent unlinked from student successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": StudentNotFoundExceptionResponse,
            "description": "Student not found.",
        },
    },
)
async def unlink_parent(
    student_id: Annotated[UUID, Path()],
    parent_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    if not StudentRepository.exists(connection, student_id):
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentNotFoundExceptionResponse(context={"parameter": "student_id"})

    await StudentRepository.remove_parent(connection, student_id, parent_id)
    response.status_code = status.HTTP_204_NO_CONTENT
    return


@router.post(
    "/{student_id}/enrollment",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": StudentEnrollResponse,
            "description": "Student enrolled in batch successfully.",
        },
        status.HTTP_404_NOT_FOUND: {
            "model": Union[
                StudentNotFoundExceptionResponse, BatchNotFoundExceptionResponse
            ],
            "description": "Entity not found.",
        },
        status.HTTP_409_CONFLICT: {
            "model": StudentAlreadyExistsExceptionResponse,
            "description": "Student already enrolled in the batch.",
        },
    },
)
async def enroll_student(
    student_id: Annotated[UUID, Path()],
    body: Annotated[StudentEnrollRequest, Body()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    try:
        enrollment_no = await StudentRepository.enroll_student(
            connection, student_id, body.batch_id
        )
        response.status_code = status.HTTP_201_CREATED
        return StudentEnrollResponse(enrollment_no=enrollment_no)
    except StudentNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return StudentNotFoundExceptionResponse(context=e.context)
    except BatchNotFoundException as e:
        response.status_code = status.HTTP_404_NOT_FOUND
        return BatchNotFoundExceptionResponse(context=e.context)
    except StudentAlreadyExistsException as e:
        response.status_code = status.HTTP_409_CONFLICT
        return StudentAlreadyExistsExceptionResponse(context=e.context)


@router.get(
    "/{student_id}/enrollment",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {
            "model": ListStudentEnrollmentResponse,
            "description": "List of student enrollments retrieved successfully.",
        }
    },
)
async def get_student_batches(
    student_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    enrollments = await StudentRepository.get_enrollments(connection, student_id)
    return ListStudentEnrollmentResponse(
        enrollments=[
            ListStudentEnrollmentResponse.Enrollment(
                enrollment_no=enrollment["enrollment_no"],
                batch_id=enrollment["batch_id"],
                batch_name=enrollment["batch_name"],
                batch_code=enrollment["batch_code"],
                year=enrollment["year"],
                program_name=enrollment["program_name"],
            )
            for enrollment in enrollments
        ]
    )


@router.delete(
    "/{student_id}/enrollment/{batch_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_204_NO_CONTENT: {
            "model": None,
            "description": "Student enrollment deleted successfully.",
        },
    },
)
async def delete_student_enrollment(
    student_id: Annotated[UUID, Path()],
    batch_id: Annotated[UUID, Path()],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    response: Response,
):
    await StudentRepository.delete_student_enrollment(connection, student_id, batch_id)
    response.status_code = status.HTTP_204_NO_CONTENT
    return
