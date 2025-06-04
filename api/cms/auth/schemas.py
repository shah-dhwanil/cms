from typing import Any
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email_id: EmailStr
    password: str


class LoginResponse(BaseModel):
    token: UUID
    max_age: int = 900


class CredentialsNotFoundResponse(BaseModel):
    slug: str = "credentials_not_found"
    description: str = "Authentication Credentials not found"
    context: dict[str, Any]


class NotAuthorizedResponse(BaseModel):
    slug: str = "not_authorized"
    description: str = "Your are not authorized to perform the action"
    context: dict[str, Any] = Field(
        examples=[
            {"reason": "Session is invalid or expired"},
            {"reason": "Not enough permissions"},
        ]
    )
