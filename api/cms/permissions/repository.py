from typing import Any
from asyncpg import Connection
from asyncpg.exceptions import ForeignKeyViolationError, UniqueViolationError
from cms.permissions.exceptions import (
    PermissionAlreadyExists,
    PermissionDoesNotExist,
    PermissionReferenced,
)


class PermissionRepository:
    @staticmethod
    async def create(conn: Connection, name: str, description: str) -> None:
        try:
            await conn.execute(
                """ --sql
                INSERT INTO permissions (
                    name, 
                    description
                )
                VALUES ($1, $2)
                """,
                name,
                description,
            )
        except UniqueViolationError:
            raise PermissionAlreadyExists()

    @staticmethod
    async def get_all(conn: Connection) -> list[dict[str, Any]]:
        return await conn.fetch(
            """ --sql
            SELECT name,description FROM permissions;
            """
        )

    @staticmethod
    async def delete(conn: Connection, name: str) -> None:
        try:
            result = await conn.execute(
                """ --sql
                DELETE FROM permissions
                WHERE name = $1;
                """,
                name,
            )
            if result == "DELETE 0":
                raise PermissionDoesNotExist()
        except ForeignKeyViolationError:
            raise PermissionReferenced("delete")
