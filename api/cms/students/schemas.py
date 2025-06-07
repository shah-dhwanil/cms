from typing import Optional
from uuid import UUID
from cms.students.exceptions import StudentAlreadyExists
from pydantic import BaseModel, Field


class CreateStudentRequest(BaseModel):
    user_id: UUID
    first_name: str = Field(max_length=16)
    last_name: str = Field(max_length=16)
    gender: str = Field(min_length=1, max_length=1)
    aadhaar_no: str = Field(pattern=r"[0-9]{12}",min_length=12, max_length=12)
    apaar_id: str = Field(pattern=r"[0-9]{12}",min_length=12, max_length=12)


class GetStudentResponse(BaseModel):
    id:UUID
    first_name: str = Field(max_length=16)
    last_name: str = Field(max_length=16)
    gender: str = Field(min_length=1, max_length=1)
    aadhaar_no: str = Field(pattern=r"[0-9]{12}", min_length=12, max_length=12)
    apaar_id: str = Field(pattern=r"[0-9]{12}", min_length=12, max_length=12)
    active:bool


class UpdateStudentRequest(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=16)
    last_name: Optional[str] = Field(default=None, max_length=16)
    gender: Optional[str] = Field(default=None, min_length=1, max_length=1)
    aadhaar_no: Optional[str] = Field(
        default=None, pattern=r"[0-9]{12}", min_length=12, max_length=12
    )
    apaar_id: Optional[str] = Field(
        default=None, pattern=r"[0-9]{12}", min_length=12, max_length=12
    )


class StudentDoesNotExistsResponse(BaseModel):
    slug: str = StudentAlreadyExists.slug
    description: str = StudentAlreadyExists.description
    context: dict = Field(examples=[{"identifier": "id"}])


class StudentAlreadyExistsResponse(BaseModel):
    slug: str = StudentAlreadyExists.slug
    description: str = StudentAlreadyExists.description
    context: dict = Field(examples=[{"identifier": "id"}])
