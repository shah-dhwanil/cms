from typing import Any, Dict, List, Optional
from uuid import UUID

from cms.batch.exceptions import (
    BatchAlreadyExistsException,
    BatchNotFoundException,
)
from pydantic import BaseModel, Field

__all__ = [
    "Batch",
    "CreateBatchRequest",
    "CreateBatchResponse",
    "UpdateBatchRequest",
    "GetBatchRequest",
    "ListBatchResponse",
    "BatchNotFoundExceptionResponse",
    "BatchAlreadyExistsExceptionResponse",
]


class Batch(BaseModel):
    id: UUID
    code: str = Field(..., max_length=32)
    program_id: UUID
    program_name: str
    name: str = Field(..., max_length=32)
    year: int
    extra_info: Optional[Dict[str, Any]] = None


class CreateBatchRequest(BaseModel):
    code: str = Field(..., max_length=32)
    program_id: UUID
    name: str = Field(..., max_length=32)
    year: int = Field(
        ..., ge=1900, le=2100, description="Year must be between 1900 and 2100"
    )
    extra_info: Optional[Dict[str, Any]] = None


class CreateBatchResponse(BaseModel):
    id: UUID


class GetBatchRequest(BaseModel):
    program_id: Optional[UUID] = None
    year: Optional[int] = Field(
        None, ge=1900, le=2100, description="Year must be between 1900 and 2100"
    )
    limit: Optional[int] = 100
    offset: Optional[int] = 0


class UpdateBatchRequest(BaseModel):
    code: Optional[str] = Field(None, max_length=32)
    program_id: Optional[UUID] = None
    name: Optional[str] = Field(None, max_length=32)
    year: Optional[int] = Field(
        None, ge=1900, le=2100, description="Year must be between 1900 and 2100"
    )
    extra_info: Optional[Dict[str, Any]] = None


class ListBatchResponse(BaseModel):
    batches: List[Batch] = Field(..., description="List of batches")


class BatchNotFoundExceptionResponse(BaseModel):
    slug: str = BatchNotFoundException.slug
    description: str = BatchNotFoundException.description
    context: dict


class BatchAlreadyExistsExceptionResponse(BaseModel):
    slug: str = BatchAlreadyExistsException.slug
    description: str = BatchAlreadyExistsException.description
    context: dict


class ListEnrolledStudentsResponse(BaseModel):
    class Student(BaseModel):
        id: UUID
        enrollment_no: str
        first_name: str
        middle_name: str
        last_name: str

    students: List[Student] = Field(
        ..., description="List of enrolled students in the batch"
    )
