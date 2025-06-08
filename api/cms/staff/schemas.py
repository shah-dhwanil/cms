from typing import Any, Optional
from uuid import UUID

from cms.staff.exceptions import StaffAlreadyExists, StaffDoesNotExists
from pydantic import BaseModel, Field


class CreateStaffRequest(BaseModel):
    user_id: UUID
    first_name: str = Field(..., max_length=16)
    last_name: str = Field(..., max_length=16)
    position: str = Field(..., max_length=64)
    education: dict[str, Any]
    experience: dict[str, Any]
    activity: dict[str, Any]
    other_details: Optional[dict[str, Any]] = None
    public: bool = True


class GetStaffResponse(BaseModel):
    user_id: UUID
    first_name: str
    last_name: str
    position: str
    education: dict
    experience: dict
    activity: dict
    other_details: Optional[dict]
    public: bool
    active: bool


class UpdateStaffRequest(BaseModel):
    first_name: Optional[str] = Field(default=None, max_length=16)
    last_name: Optional[str] = Field(default=None, max_length=16)
    position: Optional[str] = Field(default=None, max_length=64)
    education: Optional[dict] = None
    experience: Optional[dict] = None
    activity: Optional[dict] = None
    other_details: Optional[dict] = None
    public: Optional[bool] = None


class StaffDoesNotExistsResponse(BaseModel):
    slug: str = StaffDoesNotExists.slug
    description: str = StaffDoesNotExists.description
    context: dict[str, Any] = Field(examples=[{"identifier": "user_id"}])


class StaffAlreadyExistsResponse(BaseModel):
    slug: str = StaffAlreadyExists.slug
    description: str = StaffAlreadyExists.description
    context: dict[str, Any] = Field(examples=[{"identifier": "user_id"}])
