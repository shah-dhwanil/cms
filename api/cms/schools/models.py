from typing import Any, Dict, List, Optional
from uuid import UUID

from cms.schools.exceptions import (
    SchoolAlreadyExistsException,
    SchoolNotFoundException,
)
from pydantic import BaseModel, Field

__all__ = [
    "School",
    "CreateSchoolRequest",
    "CreateSchoolResponse",
    "UpdateSchoolRequest",
    "ListSchoolResponse",
    "SchoolNotFoundExceptionResponse",
    "SchoolAlreadyExistsExceptionResponse",
]


class School(BaseModel):
    school_id: UUID
    name: str = Field(..., max_length=128)
    dean_id: UUID
    extra_info: Optional[Dict[str, Any]] = None


class CreateSchoolRequest(BaseModel):
    name: str = Field(..., max_length=128)
    dean_id: UUID
    extra_info: Optional[Dict[str, Any]] = None


class CreateSchoolResponse(BaseModel):
    school_id: UUID


class UpdateSchoolRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    dean_id: Optional[UUID] = None
    extra_info: Optional[Dict[str, Any]] = None


class ListSchoolResponse(BaseModel):
    schools: List[School] = Field(..., description="List of schools")


class SchoolNotFoundExceptionResponse(BaseModel):
    slug: str = SchoolNotFoundException.slug
    description: str = SchoolNotFoundException.description
    context: dict


class SchoolAlreadyExistsExceptionResponse(BaseModel):
    slug: str = SchoolAlreadyExistsException.slug
    description: str = SchoolAlreadyExistsException.description
    context: dict
