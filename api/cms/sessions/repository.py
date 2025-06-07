from typing import Any, Optional
from asyncpg import Connection
from uuid import UUID

from asyncpg.exceptions import ForeignKeyViolationError
from cms.sessions.exceptions import SessionDoesNotExists
from cms.users.exceptions import UserNotExists


class SessionRepository:
    @staticmethod
    async def create_session(
        conn: Connection,
        user_id: UUID,
    ) -> UUID:
        try:
            session_id = await conn.fetchval(
                """
                INSERT INTO sessions(user_id)
                VALUES ($1)
                RETURNING id
                """,
                user_id,
            )
            return UUID(str(session_id))
        except ForeignKeyViolationError:
            raise UserNotExists(identifier="user_id")

    @staticmethod
    async def get_all_sessions(
        conn: Connection,
    ) -> list[dict[str, Any]]:
        sessions = await conn.fetch(
            """
            SELECT id,user_id,created_at,expires_at,terminated
            FROM sessions;
            """
        )
        return sessions

    @staticmethod
    async def get_session(conn: Connection, session_id: UUID) -> dict[str, Any]:
        session = await conn.fetchrow(
            """
            SELECT id,user_id,created_at,expires_at,terminated
            FROM sessions
            WHERE id = $1;
            """,
            session_id,
        )
        if session is None:
            raise SessionDoesNotExists()
        return session

    @staticmethod
    async def verify_session(conn: Connection, session_id: UUID) -> Optional[UUID]:
        user_id = await conn.fetchval(
            """
            SELECT user_id
            FROM sessions
            WHERE id = $1 AND expires_at > NOW() AND terminated = FALSE;
            """,
            session_id,
        )
        return user_id

    @staticmethod
    async def terminate_session(conn: Connection, session_id: UUID) -> None:
        result = await conn.execute(
            """
            UPDATE sessions
            SET terminated = TRUE
            WHERE id = $1;
            """,
            session_id,
        )
        if result == "UPDATE 0":
            raise SessionDoesNotExists()
        return None
