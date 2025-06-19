from cms.users.exceptions import (
    PasswordIncorrectException,
    UserAlreadyExistsException,
    UserNotFoundException,
)
from pydantic import BaseModel, Field, EmailStr
from pydantic_extra_types.phone_numbers import PhoneNumber
from typing import Optional, List
from uuid import UUID

__all__ = [
    "User",
    "CreateUserRequest",
    "CreateUserResponse",
    "UpdateUserRequest",
    "UpdateUserPasswordRequest",
    "ListUserResponse",
    "UserNotFoundExceptionResponse",
    "UserAlreadyExistsExceptionResponse",
    "PasswordIncorrectExceptionResponse",
    "GrantPermissionRequest",
    "RevokePermissionRequest",
    "ListUserPermissionsResponse",
]

PhoneNumber.phone_format = "INTERNATIONAL"
PhoneNumber.default_region_code = "IN"


class User(BaseModel):
    user_id: UUID
    email_id: EmailStr = Field(..., max_length=64)
    contact_no: PhoneNumber = Field(..., max_length=20)
    profile_image_id: Optional[UUID] = None


class CreateUserRequest(BaseModel):
    email_id: EmailStr = Field(..., max_length=64)
    password: str = Field(..., min_length=8, max_length=32)
    contact_no: PhoneNumber = Field(..., max_length=20)
    profile_image_id: Optional[UUID] = None


class CreateUserResponse(BaseModel):
    user_id: UUID


class UpdateUserRequest(BaseModel):
    contact_no: Optional[PhoneNumber] = Field(None, max_length=20)
    profile_image_id: Optional[UUID] = None


class UpdateUserPasswordRequest(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=32)
    new_password: str = Field(..., min_length=8, max_length=32)


class ListUserResponse(BaseModel):
    users: List[User] = Field(..., description="List of users")


class UserNotFoundExceptionResponse(BaseModel):
    slug: str = UserNotFoundException.slug
    description: str = UserNotFoundException.description
    context: dict


class UserAlreadyExistsExceptionResponse(BaseModel):
    slug: str = UserAlreadyExistsException.slug
    description: str = UserAlreadyExistsException.description
    context: dict


class PasswordIncorrectExceptionResponse(BaseModel):
    slug: str = PasswordIncorrectException.slug
    description: str = PasswordIncorrectException.description
    context: dict


class GrantPermissionRequest(BaseModel):
    permissions: List[str] = Field(
        ..., description="List of permission slugs to assign"
    )


class RevokePermissionRequest(BaseModel):
    permissions: List[str] = Field(
        ..., description="List of permission slugs to remove"
    )


class ListUserPermissionsResponse(BaseModel):
    permissions: List[str] = Field(
        ..., description="List of permission slugs assigned to the user"
    )
