from typing import Any, Dict, List, Optional
from uuid import UUID

from cms.departments.exceptions import (
    DepartmentAlreadyExistsException,
    DepartmentNotFoundException,
)
from pydantic import BaseModel, Field

__all__ = [
    "Department",
    "CreateDepartmentRequest",
    "CreateDepartmentResponse",
    "UpdateDepartmentRequest",
    "ListDepartmentResponse",
    "DepartmentNotFoundExceptionResponse",
    "DepartmentAlreadyExistsExceptionResponse",
]


class Department(BaseModel):
    id: UUID
    name: str = Field(..., max_length=128)
    school_id: UUID
    head_id: UUID
    extra_info: Optional[Dict[str, Any]] = None


class CreateDepartmentRequest(BaseModel):
    name: str = Field(..., max_length=128)
    school_id: UUID
    head_id: UUID
    extra_info: Optional[Dict[str, Any]] = None


class CreateDepartmentResponse(BaseModel):
    id: UUID


class UpdateDepartmentRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    school_id: Optional[UUID] = None
    head_id: Optional[UUID] = None
    extra_info: Optional[Dict[str, Any]] = None


class ListDepartmentResponse(BaseModel):
    departments: List[Department] = Field(..., description="List of departments")


class DepartmentNotFoundExceptionResponse(BaseModel):
    slug: str = DepartmentNotFoundException.slug
    description: str = DepartmentNotFoundException.description
    context: dict


class DepartmentAlreadyExistsExceptionResponse(BaseModel):
    slug: str = DepartmentAlreadyExistsException.slug
    description: str = DepartmentAlreadyExistsException.description
    context: dict
