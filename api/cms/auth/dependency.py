from typing import Annotated, Optional
from uuid import UUID
from cms.auth.exceptions import CredentialsNotFound, NotEnoughPermissions, SessionInvalidOrExpired
from cms.users.repository import UserRepository
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cms.utils.postgres import PgPool
from cms.sessions.repository import SessionRepository
from asyncpg import Connection
from fastapi import Depends, Security

bearer = HTTPBearer(auto_error=False)


async def get_session_id(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Security(bearer)],
) -> UUID:
    if credentials is None or credentials.credentials is None:
        raise CredentialsNotFound()
    try:
        session_id = UUID(credentials.credentials)
    except ValueError:
        raise CredentialsNotFound()
    return session_id


async def requires_active_session(
    session_id: Annotated[UUID, Depends(get_session_id)],
    connection: Annotated[Connection, Depends(PgPool.get_connection)],
) -> UUID:
    print("Dependency called!!!")
    result = await SessionRepository.verify_session(connection, session_id)
    if result is None:
        raise SessionInvalidOrExpired()
    return result

class PermissionRequired():
    def __init__(self, permissions: list[str]):
        self.permissions = permissions
    
    async def __call__(self, connection:Annotated[Connection,Depends(PgPool.get_connection)],user_id:Annotated[UUID,Depends(requires_active_session)]):
        result = await UserRepository.user_has_permissions(connection,user_id,self.permissions)
        if not result:
            raise NotEnoughPermissions()