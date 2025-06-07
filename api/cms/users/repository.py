from typing import Any, Optional
from uuid import UUID

from asyncpg import Connection
from asyncpg.exceptions import ForeignKeyViolationError, UniqueViolationError

from cms.permissions.exceptions import PermissionDoesNotExist
from cms.users.exceptions import UserAlreadyExists, UserDoesNotExists


class UserRepository:
    @staticmethod
    async def create(
        connection: Connection,
        uid: UUID,
        email_id: str,
        password: str,
        contact_no: str,
        profile_image: UUID,
        *args,
        **kwargs,
    ) -> None:
        try:
            await connection.execute(
                """--sql
                INSERT INTO users(
                    id,
                    email_id,
                    password,
                    contact_no,
                    profile_image
                )
                VALUES($1,$2,$3,$4,$5);
                """,
                uid,
                email_id,
                password,
                contact_no,
                profile_image,
            )
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_users_email_id":
                    raise UserAlreadyExists(identifier="email_id")
                case "uniq_users_contact_no":
                    raise UserAlreadyExists(identifier="contact_no")
                case _:
                    raise UserAlreadyExists(identifier="unkown")

    @staticmethod
    async def get_by_id(
        connection: Connection, uid: UUID, *args, **kwargs
    ) -> dict[str, Any]:
        result = await connection.fetchrow(
            """--sql
            SELECT id,email_id,password,contact_no,profile_image FROM users WHERE id = $1 AND active = TRUE;
            """,
            uid,
        )
        if result is None:
            raise UserDoesNotExists(identifier="id")
        return result

    @staticmethod
    async def get_by_email_id(
        connection: Connection, email_id: str, *args, **kwargs
    ) -> dict[str, Any]:
        result = await connection.fetchrow(
            """--sql
            SELECT id,email_id,password,contact_no,profile_image FROM users WHERE email_id = $1 AND active = TRUE;
            """,
            email_id,
        )
        if result is None:
            raise UserDoesNotExists(identifier="email_id")
        return result

    @staticmethod
    async def update(
        connection: Connection,
        uid: UUID,
        password: Optional[str] = None,
        contact_no: Optional[str] = None,
        profile_image: Optional[str] = None,
        *args,
        **kwargs,
    ) -> None:
        result = await connection.execute(
            """--sql
            UPDATE users 
            SET 
                password = COALESCE($1,password),
                contact_no = COALESCE($2,contact_no),
                profile_image = COALESCE($3,profile_image)
            WHERE id = $4 AND active = TRUE;
            """,
            password,
            contact_no,
            profile_image,
            uid,
        )
        if result == "UPDATE 0":
            raise UserDoesNotExists(identifier="id")

    @staticmethod
    async def delete(connection: Connection, uid: UUID, *args, **kwargs) -> None:
        result = await connection.execute(
            """--sql
            UPDATE users SET active = FALSE WHERE id = $1;
            """,
            uid,
        )
        if result == "UPDATE 0":
            raise UserDoesNotExists(identifier="id")

    @staticmethod
    async def grant_permissions(
        connection: Connection, uid: UUID, permissions: list[str], *args, **kwargs
    ) -> None:
        # No need to use transactions as executemany is atomic operation
        try:
            await connection.executemany(
                """
                INSERT INTO user_permissions (user_id, permission_name)
                VALUES ($1, $2)
                ON CONFLICT (user_id, permission_name) DO NOTHING;
                """,
                [(uid, permission) for permission in permissions],
            )
        except ForeignKeyViolationError as e:
            if e.as_dict()["constraint_name"] == "fk_user_permissions_permissions":
                val = e.as_dict()["detail"].split("=")[1].split(")")[0][1::]
                raise PermissionDoesNotExist({"value": val})
            else:
                raise UserDoesNotExists(identifier="id")

    @staticmethod
    async def revoke_permissions(
        connection: Connection, uid: UUID, permissions: list[str], *args, **kwargs
    ) -> None:
        # No need to use transactions as executemany is atomic operation
        await connection.executemany(
            """
            DELETE FROM user_permissions WHERE user_id = $1 AND permission_name = $2;
            """,
            [(uid, permission) for permission in permissions],
        )

    @staticmethod
    async def get_user_permissions(
        connection: Connection, uid: UUID, *args, **kwargs
    ) -> list[dict[str, Any]]:
        return await connection.fetch(
            """--sql
            SELECT permission_name FROM user_permissions WHERE user_id = $1;
            """,
            uid,
        )
