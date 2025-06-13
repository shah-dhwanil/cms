from typing import Any, Optional
from asyncpg import Connection, ForeignKeyViolationError, UniqueViolationError

from cms.permissions.exceptions import (
    PermissionAlreadyExistsException,
    PermissionNotFoundException,
    PermissionStillReferencedException,
)

__all__ = ["PermissionRepository"]


class PermissionRepository:
    @staticmethod
    async def create(connection: Connection, slug: str, description: str) -> None:
        try:
            await connection.execute(
                """--sql
                INSERT INTO permissions(slug, description)
                VALUES($1, $2);
                """,
                slug,
                description,
            )
        except UniqueViolationError as e:
            details = e.as_dict()
            if details["constraint_name"] == "pk_permissions":
                raise PermissionAlreadyExistsException(parameter="slug")
            raise Exception(details)  # Or a more generic DB error

    @staticmethod
    async def get_by_slug(connection: Connection, slug: str) -> dict[str, Any]:
        record = await connection.fetchrow(
            """--sql
            SELECT slug, description
            FROM permissions
            WHERE slug = $1;
            """,
            slug,
        )
        if record is None:
            raise PermissionNotFoundException(parameter="slug")
        return dict(record)

    @staticmethod
    async def get_all(
        connection: Connection, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT slug, description
            FROM permissions
            ORDER BY slug ASC
            LIMIT $1 OFFSET $2;
            """,
            limit,
            offset,
        )
        return [dict(record) for record in records]

    @staticmethod
    async def update(
        connection: Connection, slug: str, description: Optional[str] = None
    ) -> None:
        if description is None:  # Nothing to update
            return

        response = await connection.execute(
            """--sql
            UPDATE permissions
            SET description = $2
            WHERE slug = $1;
            """,
            slug,
            description,
        )
        if response == "UPDATE 0":
            raise PermissionNotFoundException(parameter="slug")

    @staticmethod
    async def delete(connection: Connection, slug: str) -> None:
        try:
            await connection.execute(
                """--sql
                DELETE FROM permissions
                WHERE slug = $1;
                """,
                slug,
            )
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            if details["constraint_name"] == "fk_user_permissions_permissions":
                raise PermissionStillReferencedException(referenced_by="users")
            raise e
