from datetime import date
from typing import Any, Dict, List, Optional
from uuid import UUID

from cms.students.exceptions import (
    StudentAlreadyExistsException,
    StudentNotFoundException,
)
from pydantic import BaseModel, EmailStr, Field, HttpUrl
from pydantic_extra_types.phone_numbers import PhoneNumber

__all__ = [
    "Student",
    "CreateStudentRequest",
    "CreateStudentResponse",
    "UpdateStudentRequest",
    "ListStudentResponse",
    "StudentNotFoundExceptionResponse",
    "StudentAlreadyExistsExceptionResponse",
]

PhoneNumber.phone_format = "INTERNATIONAL"
PhoneNumber.default_region_code = "IN"


class Student(BaseModel):
    id: UUID
    first_name: str = Field(..., max_length=32)
    middle_name: str = Field(..., max_length=32)
    last_name: str = Field(..., max_length=32)
    date_of_birth: date
    gender: str = Field(..., max_length=1)
    address: str
    email_id: EmailStr = Field(..., max_length=64)
    contact_no: PhoneNumber = Field(..., max_length=20)
    aadhaar_no: str = Field(..., pattern=r"^[0-9]{12}$", min_length=12, max_length=12)
    apaar_id: str = Field(..., pattern=r"^[0-9]{12}$", min_length=12, max_length=12)
    extra_info: Optional[Dict[str, Any]] = None


class CreateStudentRequest(BaseModel):
    first_name: str = Field(..., max_length=32)
    middle_name: str = Field(..., max_length=32)
    last_name: str = Field(..., max_length=32)
    date_of_birth: date
    gender: str = Field(..., max_length=1)
    address: str
    email_id: EmailStr = Field(..., max_length=64)
    contact_no: PhoneNumber = Field(..., max_length=20)
    aadhaar_no: str = Field(..., pattern=r"^[0-9]{12}$", min_length=12, max_length=12)
    apaar_id: str = Field(..., pattern=r"^[0-9]{12}$", min_length=12, max_length=12)
    extra_info: Optional[Dict[str, Any]] = None


class CreateStudentResponse(BaseModel):
    student_id: UUID


class UpdateStudentRequest(BaseModel):
    first_name: Optional[str] = Field(None, max_length=32)
    midlle_name: Optional[str] = Field(None, max_length=32)
    last_name: Optional[str] = Field(None, max_length=32)
    date_of_birth: Optional[date] = None
    gender: Optional[str] = Field(None, max_length=1)
    address: Optional[str] = None
    aadhaar_no: Optional[str] = Field(
        None, pattern=r"^[0-9]{12}$", min_length=12, max_length=12
    )
    apaar_id: Optional[str] = Field(
        None, pattern=r"^[0-9]{12}$", min_length=12, max_length=12
    )
    extra_info: Optional[Dict[str, Any]] = None


class ListStudentResponse(BaseModel):
    students: List[Student] = Field(..., description="List of students")


class GetStudentAdhaarResponse(BaseModel):
    url: HttpUrl


class GetStudentApaarResponse(BaseModel):
    url: HttpUrl


class StudentNotFoundExceptionResponse(BaseModel):
    slug: str = StudentNotFoundException.slug
    description: str = StudentNotFoundException.description
    context: dict


class StudentAlreadyExistsExceptionResponse(BaseModel):
    slug: str = StudentAlreadyExistsException.slug
    description: str = StudentAlreadyExistsException.description
    context: dict


class StudentEnrollRequest(BaseModel):
    batch_id: UUID


class StudentEnrollResponse(BaseModel):
    enrollment_no: str


class ListStudentEnrollmentResponse(BaseModel):
    class Enrollment(BaseModel):
        enrollment_no: str
        batch_id: UUID
        batch_name: str
        batch_code: str
        year: int
        program_name: str

    enrollments: List[Enrollment] = Field(
        ..., description="List of student enrollments"
    )
