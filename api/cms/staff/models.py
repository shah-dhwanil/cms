from typing import Any, Dict, List, Optional
from uuid import UUID

from cms.staff.exceptions import StaffAlreadyExistsException, StaffNotFoundException
from pydantic import BaseModel, EmailStr, Field
from pydantic_extra_types.phone_numbers import PhoneNumber


__all__ = [
    "Staff",
    "CreateStaffRequest",
    "CreateStaffResponse",
    "UpdateStaffRequest",
    "ListStaffResponse",
    "StaffNotFoundExceptionResponse",
    "StaffAlreadyExistsExceptionResponse",
]

PhoneNumber.phone_format = "INTERNATIONAL"
PhoneNumber.default_region_code = "IN"


class Staff(BaseModel):
    id: UUID
    first_name: str = Field(..., max_length=32)
    last_name: str = Field(..., max_length=32)
    email_id: Optional[EmailStr] = None
    contact_no: PhoneNumber = (Field(..., max_length=20),)
    position: str = Field(..., max_length=64)
    education: Dict[str, Any]
    experience: Dict[str, Any]
    activity: Dict[str, Any]
    other_details: Optional[Dict[str, Any]] = None
    is_public: bool = True


class CreateStaffRequest(BaseModel):
    first_name: str = Field(..., max_length=32)
    last_name: str = Field(..., max_length=32)
    email_id: EmailStr = Field(..., max_length=64)
    contact_no: PhoneNumber = Field(..., max_length=20)
    position: str = Field(..., max_length=64)
    education: Dict[str, Any]
    experience: Dict[str, Any]
    activity: Dict[str, Any]
    other_details: Optional[Dict[str, Any]] = None
    is_public: bool = True


class CreateStaffResponse(BaseModel):
    staff_id: UUID


class UpdateStaffRequest(BaseModel):
    first_name: Optional[str] = Field(None, max_length=32)
    last_name: Optional[str] = Field(None, max_length=32)
    position: Optional[str] = Field(None, max_length=64)
    education: Optional[Dict[str, Any]] = None
    experience: Optional[Dict[str, Any]] = None
    activity: Optional[Dict[str, Any]] = None
    other_details: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


class ListStaffResponse(BaseModel):
    staff: List[Staff] = Field(..., description="List of staff members")


class StaffNotFoundExceptionResponse(BaseModel):
    slug: str = StaffNotFoundException.slug
    description: str = StaffNotFoundException.description
    context: dict


class StaffAlreadyExistsExceptionResponse(BaseModel):
    slug: str = StaffAlreadyExistsException.slug
    description: str = StaffAlreadyExistsException.description
    context: dict
