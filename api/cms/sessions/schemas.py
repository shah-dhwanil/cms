from cms.sessions.exceptions import SessionDoesNotExists
from pydantic import BaseModel
from uuid import UUID


class CreateSessionRequest(BaseModel):
    user_id: UUID


class CreateSessionsResponse(BaseModel):
    session_id: UUID


class GetSessionResponse(BaseModel):
    session_id: UUID
    user_id: UUID
    created_at: str
    expires_at: str
    terminated: bool


class SessionDoesNotExistsResponse(BaseModel):
    slug: str = SessionDoesNotExists.slug
    message: str = SessionDoesNotExists.message
    context: dict[str, str]
