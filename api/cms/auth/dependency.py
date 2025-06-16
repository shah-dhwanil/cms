from typing import Optional, Annotated
from fastapi import Request
from uuid import UUID
from asyncpg import Connection
from cms.auth.models import Session
from cms.sessions.repository import SessionRepository, UserNotFoundException
from cms.sessions.exceptions import SessionNotFoundException
from cms.sessions.utils import get_client_ip
from cms.users.repository import UserRepository
from cms.utils.hash import verify_hash
from cms.utils.postgres import PgPool
from cms.auth.exceptions import (
    CredentialsNotFoundException,
    NotEnoughPermissionsException,
    SessionInvalidOrExpiredException,
)
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)


async def get_session_id(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer)],
) -> UUID:
    if credentials is None or credentials.credentials is None:
        raise CredentialsNotFoundException()
    try:
        session_id = UUID(credentials.credentials)
    except ValueError:
        raise CredentialsNotFoundException()
    return session_id


async def get_session(
    session_id: Annotated[UUID, Depends(get_session_id)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
    request: Request,
) -> Session:
    try:
        session = await SessionRepository.get_by_id(connection, session_id)
        permissions = await UserRepository.get_user_permissions(
            connection, session["user_id"]
        )
    except SessionNotFoundException:
        await connection.close()
        raise SessionInvalidOrExpiredException()
    except UserNotFoundException:
        await connection.close()
        raise SessionInvalidOrExpiredException()
    except Exception as e:
        await connection.close()
        raise e
    if verify_hash(get_client_ip(request), session["ip_addr"]):
        return Session(
            session_id=session["session_id"],
            user=Session.User(
                user_id=session["user_id"],
                permissions=[record["permission"] for record in permissions],
            ),
        )
    await connection.close()
    raise SessionInvalidOrExpiredException()


class RequiresPermission:
    def __init__(self, *required_permissions: str):
        self.required_permissions = required_permissions

    async def __call__(
        self,
        session: Annotated[Session, Depends(get_session)],
    ) -> None:
        result = all(
            permission in session.user.permissions
            for permission in self.required_permissions
        )
        if not result:
            raise NotEnoughPermissionsException()


class RequiresAnyOfGivenPermission:
    def __init__(self, *permissions: list[str]):
        self.permissions = permissions

    async def __call__(
        self,
        session: Annotated[Session, Depends(get_session)],
    ) -> list[str]:
        for permission in self.permissions:
            result = all(
                permission_name in session.user.permissions
                for permission_name in permission
            )
            if result:
                return permission
        raise NotEnoughPermissionsException()
