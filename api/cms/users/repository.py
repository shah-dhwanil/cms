from typing import Any, Optional
from uuid import UUID

from asyncpg import Connection, ForeignKeyViolationError, UniqueViolationError
from cms.permissions.exceptions import PermissionNotFoundException
from cms.users.exceptions import UserAlreadyExistsException, UserNotFoundException
from uuid_utils.compat import uuid7

__all__ = ["UserRepository"]


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
            SELECT id,email_id,password,contact_no,profile_image_id,is_active
            FROM users
            WHERE id = $1 AND is_active = TRUE;
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
            SELECT id,email_id,password,contact_no,profile_image_id,is_active
            FROM users
            WHERE email_id = $1 AND is_active = TRUE;
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
            SELECT id,email_id,contact_no,profile_image_id,is_active
            FROM users
            WHERE is_active = TRUE
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
        password: Optional[str] = None,
        contact_no: Optional[str] = None,
        profile_image_id: Optional[UUID] = None,
    ) -> None:
        response = await connection.execute(
            """--sql
            UPDATE users
            SET password = COALESCE($2,password),
                contact_no = COALESCE($3, contact_no),
                profile_image_id = COALESCE($4, profile_image_id)
            WHERE id = $1 AND is_active = TRUE;
            """,
            uid,
            password,
            contact_no,
            profile_image_id,
        )
        if response != "UPDATE 1":
            raise UserNotFoundException("user_id")

    @staticmethod
    async def delete(connection: Connection, uid: UUID) -> None:
        await connection.execute(
            """--sql
            UPDATE users
            SET
                is_active = FALSE
            WHERE id = $1;
            """,
            uid,
        )

    @staticmethod
    async def grant_permissions(
        connection: Connection, user_id: UUID, permissions: list[str]
    ) -> None:
        try:
            await connection.executemany(
                """--sql
                INSERT INTO user_permissions (user_id, permission)
                VALUES ($1, $2)
                ON CONFLICT (user_id, permission) DO NOTHING;
                """,
                [(user_id, permission) for permission in permissions],
            )
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "fk_user_permissions_user":
                    raise UserNotFoundException(parameter="user_id")
                case "fk_user_permissions_permissions":
                    raise PermissionNotFoundException(parameter="permission")
                case _:
                    raise Exception(details)

    @staticmethod
    async def revoke_permissions(
        connection: Connection, user_id: UUID, permissions: list[str]
    ) -> None:
        reponse = await connection.execute(
            """--sql
            DELETE FROM user_permissions
            WHERE user_id = $1 AND permission = ANY($2);
            """,
            user_id,
            permissions,
        )
        if reponse == "DELETE 0":
            result = await connection.fetchval(
                """--sql
                SELECT TRUE FROM users WHERE id = $1 AND is_active = TRUE;
                """,
                user_id,
            )
            if not result:
                raise UserNotFoundException(parameter="user_id")

    @staticmethod
    async def get_user_permissions(
        connection: Connection, user_id: UUID
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT permission
            FROM user_permissions
            WHERE user_id = $1
            ORDER BY permission;
            """,
            user_id,
        )
        if len(records) == 0:
            result = await connection.fetchval(
                """--sql
                SELECT TRUE FROM users WHERE id = $1 AND is_active = TRUE;
                """,
                user_id,
            )
            if not result:
                raise UserNotFoundException(parameter="user_id")
        return records
