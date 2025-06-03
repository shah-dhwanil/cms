from typing import Any
from cms.permissions.exceptions import (
    PermissionAlreadyExists,
    PermissionDoesNotExist,
    PermissionReferenced,
)
from pydantic import BaseModel, Field


class CreatePermissionRequest(BaseModel):
    name: str
    description: str


class CreatePermissionResponse(BaseModel): ...


class GetPermissionRequest(BaseModel): ...


class GetPermissionResponse(BaseModel):
    class Permission(BaseModel):
        name: str
        description: str

    permissions: list[Permission] = Field(default_factory=list)


class DeletePermissionRequest(BaseModel): ...


class DeletePermissionResponse(BaseModel): ...


class PermissionAlreadyExistsResponse(BaseModel):
    slug: str = PermissionAlreadyExists.slug
    description: str = PermissionAlreadyExists.description
    context: dict[str, Any]


class PermissionDoesNotExistResponse(BaseModel):
    slug: str = PermissionDoesNotExist.slug
    description: str = PermissionDoesNotExist.description
    context: dict[str, Any]


class PermissionReferencedResponse(BaseModel):
    slug: str = PermissionReferenced.slug
    description: str = PermissionReferenced.description
    context: dict[str, Any] = Field(examples=[{"action": "delete"}])
