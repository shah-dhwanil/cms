from typing import Any, Optional
from uuid import UUID

from asyncpg import Connection, UniqueViolationError
from cms.users.exceptions import UserAlreadyExistsException, UserNotFoundException
from uuid_utils.compat import uuid7


class UserRepository:
    @staticmethod
    async def create(
        connection: Connection,
        email_id: str,
        password: str,
        contact_no: str,
        profile_image_id: Optional[UUID] = None,
    ) -> UUID:
        uid = uuid7()
        try:
            await connection.execute(
                """
                INSERT INTO users(
                    id,email_id,password,contact_no,profile_image_id
                )
                VALUES($1,$2,$3,$4,$5);
                """,
                uid,
                email_id,
                password,
                contact_no,
                profile_image_id,
            )
            return uid
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_users_email_id":
                    raise UserAlreadyExistsException(parameter="email_id")
                case "uniq_users_contact_no":
                    raise UserAlreadyExistsException(parameter="contact_no")
                case _:
                    raise Exception(details)

    @staticmethod
    async def get_by_id(connection: Connection, uid: UUID) -> dict[str, Any]:
        record = await connection.fetchrow(
            """--sql
            SELECT id,email_id,password,contact_no,profile_image_id,active
            FROM users
            WHERE id = $1 AND active = TRUE;
            """,
            uid,
        )
        if record is None:
            raise UserNotFoundException(parameter="user_id")
        return record

    @staticmethod
    async def get_by_email_id(connection: Connection, email_id: str) -> dict[str, Any]:
        record = await connection.fetchrow(
            """--sql
            SELECT id,email_id,password,contact_no,profile_image_id,active
            FROM users
            WHERE email_id = $1 AND active = TRUE;
            """,
            email_id,
        )
        if record is None:
            raise UserNotFoundException(parameter="email_id")
        return record

    @staticmethod
    async def get_all(
        connection: Connection, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT id,email_id,contact_no,profile_image_id,active
            FROM users
            WHERE active = TRUE
            ORDER BY created_at ASC
            LIMIT $1 OFFSET $2;
            """,
            limit,
            offset,
        )
        return records

    @staticmethod
    async def update(
        connection: Connection,
        uid: UUID,
        email_id: Optional[str] = None,
        password: Optional[str] = None,
        contact_no: Optional[str] = None,
        profile_image_id: Optional[UUID] = None,
    ) -> None:
        response = await connection.execute(
            """--sql
            UPDATE users
            SET email_id = COALESCE($2, email_id),
                password = COALESCE($3,password),
                contact_no = COALESCE($4, contact_no),
                profile_image_id = COALESCE($5, profile_image_id)
            WHERE id = $1;
            """,
            uid,
            email_id,
            password,
            contact_no,
            profile_image_id,
        )
        if response != "UPDATE 1":
            raise UserNotFoundException("user_id")

    @staticmethod
    async def delete(connection: Connection, uid: UUID) -> None:
        response = await connection.execute(
            """--sql
            UPDATE users
            SET
                active = FALSE
            WHERE id = $1;
            """,
            uid,
        )
        if response != "UPDATE 1":
            raise UserNotFoundException("user_id")
