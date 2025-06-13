from typing import Optional
from cms.permissions.exceptions import (
    PermissionAlreadyExistsException,
    PermissionNotFoundException,
    PermissionStillReferencedException,
)
from pydantic import BaseModel, Field

__all__ = [
    "Permission",
    "CreatePermissionRequest",
    "UpdatePermissionRequest",
    "ListPermissionResponse",
    "PermissionNotFoundExceptionResponse",
    "PermissionAlreadyExistsExceptionResponse",
]


class Permission(BaseModel):
    slug: str = Field(..., max_length=64)
    description: str = Field(..., max_length=255)


class CreatePermissionRequest(BaseModel):
    slug: str = Field(..., max_length=64)
    description: str = Field(..., max_length=255)


class UpdatePermissionRequest(BaseModel):
    description: Optional[str] = Field(None, max_length=255)


class ListPermissionResponse(BaseModel):
    permissions: list[Permission] = Field(..., description="List of permissions")


class PermissionNotFoundExceptionResponse(BaseModel):
    slug: str = PermissionNotFoundException.slug
    description: str = PermissionNotFoundException.description
    context: dict


class PermissionAlreadyExistsExceptionResponse(BaseModel):
    slug: str = PermissionAlreadyExistsException.slug
    description: str = PermissionAlreadyExistsException.description
    context: dict


class PermissionStillReferencedExceptionResponse(BaseModel):
    slug: str = PermissionStillReferencedException.slug
    description: str = PermissionStillReferencedException.description
    context: dict
