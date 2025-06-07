from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field
from pydantic.functional_validators import model_validator

from cms.users.exceptions import UserAlreadyExists, UserDoesNotExists


class CreateUserRequest(BaseModel):
    email_id: EmailStr
    password: str
    contact_no: str
    profile_image: UUID


class CreateUserResponse(BaseModel):
    id: UUID


class GetUserRequest(BaseModel):
    id: Optional[UUID] = None
    email_id: Optional[EmailStr] = None

    @model_validator(mode="after")
    def validate_request(self):
        if self.id is None and self.email_id is None:
            raise ValueError("Either id or email_id must be provided")
        elif self.id is not None and self.email_id is not None:
            raise ValueError("Both id and email_id cannot be provided")
        return self


class GetUserResponse(BaseModel):
    id: UUID
    email_id: Optional[str]
    contact_no: Optional[str]
    profile_image: UUID


class UpdateUserRequest(BaseModel):
    contact_no: Optional[str] = None
    profile_image: Optional[str] = None


class UpdatePasswordRequest(BaseModel):
    new_password: str


class UserDoesNotExistsResponse(BaseModel):
    slug: str = UserDoesNotExists.slug
    description: str = UserDoesNotExists.description
    context: dict[str, Any] = Field(examples=[{"identifiers": "id"}])


class UserAlreadyExistsResponse(BaseModel):
    slug: str = UserAlreadyExists.slug
    description: str = UserAlreadyExists.description
    context: dict[str, Any] = Field(examples=[{"identifiers": "id"}])


class GrantPermissionsRequest(BaseModel):
    permissions: list[str]


class RevokePermissionsRequest(BaseModel):
    permissions: list[str]


class GetUserPermissionResponse(BaseModel):
    permissions: list[str]
