from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import UUID

# filepath: /workspaces/cms/api/cms/programs/models.py
from cms.programs.exceptions import (
    ProgramAlreadyExistsException,
    ProgramNotFoundException,
)
from pydantic import BaseModel, Field, model_validator

__all__ = [
    "DegreeType",
    "Program",
    "CreateProgramRequest",
    "CreateProgramResponse",
    "UpdateProgramRequest",
    "ListProgramResponse",
    "ProgramNotFoundExceptionResponse",
    "ProgramAlreadyExistsExceptionResponse",
]


class DegreeType(str, Enum):
    DIPLOMA = "DIPLOMA"
    MINOR = "MINOR"
    BECHELORS = "BECHELORS"
    MASTERS = "MASTERS"
    PHD = "PHD"
    OTHERS = "OTHERS"


class Program(BaseModel):
    id: UUID
    name: str = Field(..., max_length=128)
    degree_name: str = Field(..., max_length=128)
    degree_type: DegreeType
    department_id: UUID
    department_name: str
    extra_info: Optional[Dict[str, Any]] = None


class CreateProgramRequest(BaseModel):
    name: str = Field(..., max_length=128)
    degree_name: str = Field(..., max_length=128)
    degree_type: DegreeType
    offered_by: UUID
    extra_info: Optional[Dict[str, Any]] = None


class CreateProgramResponse(BaseModel):
    id: UUID


class GetProgramRequest(BaseModel):
    department_id: Optional[UUID] = None
    school_id: Optional[UUID] = None
    offset: Optional[int] = 0
    limit: Optional[int] = 100

    @model_validator(mode="after")
    def validate_department_or_school(self) -> "GetProgramRequest":
        print(f"Department ID: {self.department_id}, School ID: {self.school_id}")
        if self.department_id and self.school_id:
            raise ValueError("Only one of department_id or school_id can be provided.")
        return self


class UpdateProgramRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=128)
    degree_name: Optional[str] = Field(None, max_length=128)
    degree_type: Optional[DegreeType] = None
    offered_by: Optional[UUID] = None
    extra_info: Optional[Dict[str, Any]] = None


class ListProgramResponse(BaseModel):
    programs: List[Program] = Field(..., description="List of programs")


class ProgramNotFoundExceptionResponse(BaseModel):
    slug: str = ProgramNotFoundException.slug
    description: str = ProgramNotFoundException.description
    context: dict


class ProgramAlreadyExistsExceptionResponse(BaseModel):
    slug: str = ProgramAlreadyExistsException.slug
    description: str = ProgramAlreadyExistsException.description
    context: dict
