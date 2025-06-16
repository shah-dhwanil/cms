from cms.auth.exceptions import CredentialsNotFoundException, _NotAuthorizedException
from pydantic import BaseModel, Field, EmailStr
from uuid import UUID
from datetime import datetime
from typing import Any, Optional

__all__ = [
    "LoginRequest",
    "LoginResponse",
    "Session",
]


class LoginRequest(BaseModel):
    email_id: EmailStr = Field(..., max_length=64, description="User email address")
    password: str = Field(..., min_length=8, max_length=32, description="User password")


class LoginResponse(BaseModel):
    class User(BaseModel):
        user_id: UUID = Field(..., description="User unique identifier")
        profile_image_id: Optional[UUID] = Field(
            None, description="User profile image ID"
        )
        permissions: list[str] = Field(default=[], description="User permissions")

    session_id: UUID = Field(..., description="Session identifier")
    user: User = Field(..., description="Authenticated user details")
    expires_at: datetime = Field(..., description="Session expiration timestamp")


class Session(BaseModel):
    class User(BaseModel):
        user_id: UUID = Field(..., description="User unique identifier")
        permissions: list[str] = Field(default=[], description="User permissions")

    session_id: UUID = Field(..., description="Session identifier")
    user: User = Field(..., description="User details associated with the session")


class RefreshSessionResponse(BaseModel):
    session_id: UUID = Field(..., description="Session identifier")
    expires_at: datetime = Field(..., description="New session expiration timestamp")


class CredentialsNotFoundExceptionResponse(BaseModel):
    slug: str = CredentialsNotFoundException.slug
    description: str = CredentialsNotFoundException.description
    context: dict[str, Any]


class NotAuthorizedExceptionResponse(BaseModel):
    slug: str = _NotAuthorizedException.slug
    description: str = _NotAuthorizedException.description
    context: dict[str, Any] = Field(
        examples=[
            {"reason": "Session is invalid or expired"},
            {"reason": "Not enough permissions"},
        ]
    )
