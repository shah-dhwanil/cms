from cms.sessions.exceptions import SessionNotFoundException
from pydantic import BaseModel, Field
from typing import List
from uuid import UUID
from datetime import datetime

__all__ = [
    "Session",
    "CreateSessionRequest",
    "CreateSessionResponse",
    "ListSessionResponse",
    "SessionNotFoundExceptionResponse",
]


class Session(BaseModel):
    session_id: UUID
    user_id: UUID
    ip_address: str = Field(..., max_length=64)
    expires_at: datetime
    is_terminated: bool


class CreateSessionRequest(BaseModel):
    user_id: UUID
    expires_at: datetime = Field(..., description="Expiration time for the session")


class CreateSessionResponse(BaseModel):
    session_id: UUID


class ListSessionResponse(BaseModel):
    sessions: List[Session] = Field(..., description="List of sessions")


class SessionNotFoundExceptionResponse(BaseModel):
    slug: str = SessionNotFoundException.slug
    description: str = SessionNotFoundException.description
    context: dict
