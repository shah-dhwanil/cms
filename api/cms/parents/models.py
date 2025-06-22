from typing import Any, Dict, List, Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field

from cms.parents.exceptions import (
    ParentNotFoundException,
    ParentAlreadyExistsException,
)
from pydantic_extra_types.phone_numbers import PhoneNumber

__all__ = [
    "Parent",
    "CreateParentRequest",
    "CreateParentResponse",
    "UpdateParentRequest",
    "ListParentResponse",
    "ParentNotFoundExceptionResponse",
    "ParentAlreadyExistsExceptionResponse",
]

PhoneNumber.phone_format = "INTERNATIONAL"
PhoneNumber.default_region_code = "IN"


class Parent(BaseModel):
    id: UUID
    fathers_name: str = Field(..., max_length=64)
    mothers_name: str = Field(..., max_length=64)
    fathers_email_id: EmailStr = Field(..., max_length=64)
    mothers_email_id: EmailStr = Field(..., max_length=64)
    fathers_contact_no: PhoneNumber = Field(..., max_length=20)
    mothers_contact_no: PhoneNumber = Field(..., max_length=20)
    address: str
    extra_info: Optional[Dict[str, Any]] = None


class CreateParentRequest(BaseModel):
    fathers_name: str = Field(..., max_length=64)
    mothers_name: str = Field(..., max_length=64)
    fathers_email_id: EmailStr = Field(..., max_length=64)
    mothers_email_id: EmailStr = Field(..., max_length=64)
    fathers_contact_no: PhoneNumber = Field(..., max_length=15)
    mothers_contact_no: PhoneNumber = Field(..., max_length=15)
    address: str
    extra_info: Optional[Dict[str, Any]] = None


class CreateParentResponse(BaseModel):
    parent_id: UUID


class UpdateParentRequest(BaseModel):
    fathers_name: Optional[str] = Field(None, max_length=64)
    mothers_name: Optional[str] = Field(None, max_length=64)
    fathers_email_id: Optional[EmailStr] = Field(None, max_length=64)
    mothers_email_id: Optional[EmailStr] = Field(None, max_length=64)
    fathers_contact_no: Optional[PhoneNumber] = Field(None, max_length=20)
    mothers_contact_no: Optional[PhoneNumber] = Field(None, max_length=20)
    address: Optional[str] = None
    extra_info: Optional[Dict[str, Any]] = None


class ListParentResponse(BaseModel):
    parents: List[Parent] = Field(..., description="List of parents")


class ParentNotFoundExceptionResponse(BaseModel):
    slug: str = ParentNotFoundException.slug
    description: str = ParentNotFoundException.description
    context: dict


class ParentAlreadyExistsExceptionResponse(BaseModel):
    slug: str = ParentAlreadyExistsException.slug
    description: str = ParentAlreadyExistsException.description
    context: dict
