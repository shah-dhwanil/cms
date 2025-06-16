from datetime import datetime
from typing import Any
from uuid import UUID
from asyncpg import Connection, ForeignKeyViolationError
from cms.users.exceptions import UserNotFoundException
from cms.sessions.exceptions import SessionNotFoundException

__all__ = ["SessionRepository"]


class SessionRepository:
    @staticmethod
    async def create(
        connection: Connection,
        user_id: UUID,
        ip_addr: str,
    ) -> dict[str, Any]:
        try:
            session = await connection.fetchrow(
                """--sql
                INSERT INTO sessions(
                    user_id, ip_addr
                )
                VALUES($1, $2)
                RETURNING session_id,expires_at;
                """,
                user_id,
                ip_addr,
            )
            return session
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "fk_sessions_users":
                    raise UserNotFoundException(parameter="user_id")
                case _:
                    raise e

    @staticmethod
    async def get_by_id(connection: Connection, session_id: UUID) -> dict[str, Any]:
        record = await connection.fetchrow(
            """--sql
            SELECT session_id, user_id, ip_addr, expires_at, is_terminated
            FROM sessions
            WHERE session_id = $1 AND expires_at > NOW() AND is_terminated = FALSE;
            """,
            session_id,
        )
        if record is None:
            raise SessionNotFoundException(parameter="session_id")
        return record

    @staticmethod
    async def get_by_user_id(
        connection: Connection, user_id: UUID
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT session_id, user_id, ip_addr, expires_at, is_terminated
            FROM sessions
            WHERE user_id = $1 AND expires_at > NOW() AND is_terminated = FALSE
            ORDER BY expires_at DESC;
            """,
            user_id,
        )
        return records

    @staticmethod
    async def terminate(connection: Connection, session_id: UUID) -> None:
        response = await connection.execute(
            """--sql
            UPDATE sessions
            SET is_terminated = TRUE
            WHERE session_id = $1;
            """,
            session_id,
        )
        if response != "UPDATE 1":
            raise SessionNotFoundException(parameter="session_id")

    @staticmethod
    async def terminate_all_user_sessions(
        connection: Connection, user_id: UUID
    ) -> None:
        await connection.execute(
            """--sql
            UPDATE sessions
            SET is_terminated = TRUE
            WHERE user_id = $1 AND expires_at > NOW();
            """,
            user_id,
        )

    @staticmethod
    async def clean_expired(connection: Connection) -> None:
        await connection.execute(
            """--sql
            DELETE FROM sessions
            WHERE expires_at + INTERVAL '1 month' < now();
            """,
        )

    @staticmethod
    async def refresh(connection: Connection, session_id: UUID) -> datetime:
        result = await connection.fetchval(
            """--sql
            UPDATE sessions
            SET expires_at = now() + INTERVAL '15 minutes'
            WHERE session_id = $1 AND expires_at > NOW() AND is_terminated = FALSE
            RETURNING expires_at;
            """,
            session_id,
        )
        if result is None:
            raise SessionNotFoundException(parameter="session_id")
        return result
