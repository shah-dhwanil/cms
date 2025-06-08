from typing import Any, Optional
from uuid import UUID
from cms.parents.exceptions import ParentAlreadyExists, ParentDoesNotExists
from pydantic import BaseModel, Field


class CreateParentRequest(BaseModel):
    user_id: UUID
    father_name: str
    mother_name: str
    address: str


class GetParentResponse(BaseModel):
    user_id: UUID
    father_name: str
    mother_name: str
    address: str
    active: bool


class UpdateParentRequest(BaseModel):
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    address: Optional[str] = None


class ParentDoesNotExistsResponse(BaseModel):
    slug: str = ParentDoesNotExists.slug
    description: str = ParentDoesNotExists.description
    context: dict[str, Any] = Field(examples=[{"identifier": "user_id"}])


class ParentAlreadyExistsResponse(BaseModel):
    slug: str = ParentAlreadyExists.slug
    description: str = ParentAlreadyExists.description
    context: dict[str, Any] = Field(examples=[{"identifier": "user_id"}])


class GetStudentResponse(BaseModel):
    id: UUID
    first_name: str
    last_name: str
