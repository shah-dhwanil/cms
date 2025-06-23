from typing import Any, Optional
from uuid import UUID

from asyncpg import Connection, ForeignKeyViolationError, UniqueViolationError
from cms.schools.exceptions import SchoolAlreadyExistsException, SchoolNotFoundException
from cms.staff.exceptions import StaffNotFoundException
from uuid_utils.compat import uuid7

__all__ = ["SchoolRepository"]


class SchoolRepository:
    @staticmethod
    async def create(
        connection: Connection,
        name: str,
        dean_id: UUID,
        extra_info: Optional[dict] = None,
    ) -> UUID:
        uid = uuid7()
        try:
            await connection.execute(
                """
                INSERT INTO school(
                    id, name, dean_id, extra_info
                )
                VALUES($1, initcap($2), $3, $4);
                """,
                uid,
                name,
                dean_id,
                extra_info,
            )
            return uid
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_school_name":
                    raise SchoolAlreadyExistsException(parameter="name")
                case "uniq_school_dean_id":
                    raise SchoolAlreadyExistsException(parameter="dean_id")
                case _:
                    raise Exception(details)
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            if details["constraint_name"] == "fk_school_dean":
                raise StaffNotFoundException(parameter="dean_id")
            raise Exception(details)

    @staticmethod
    async def exists(connection: Connection, uid: UUID) -> bool:
        result = await connection.fetchval(
            """--sql
            SELECT EXISTS(
                SELECT 1 FROM school WHERE id = $1 AND is_active = TRUE
            );
            """,
            uid,
        )
        return bool(result)

    @staticmethod
    async def get_by_id(connection: Connection, uid: UUID) -> dict[str, Any]:
        record = await connection.fetchrow(
            """--sql
            SELECT id, name, dean_id, extra_info, is_active
            FROM school
            WHERE id = $1 AND is_active = TRUE;
            """,
            uid,
        )
        if record is None:
            raise SchoolNotFoundException(parameter="school_id")
        return record

    @staticmethod
    async def get_by_name(connection: Connection, name: str) -> list[dict[str, Any]]:
        name = f"%{name}%"
        record = await connection.fetch(
            """--sql
            SELECT id, name, dean_id, extra_info, is_active
            FROM school
            WHERE name ILIKE $1 AND is_active = TRUE;
            """,
            name,
        )
        if record is None:
            raise SchoolNotFoundException(parameter="name")
        return record

    @staticmethod
    async def get_by_dean_id(connection: Connection, dean_id: UUID) -> dict[str, Any]:
        record = await connection.fetchrow(
            """--sql
            SELECT id, name, dean_id, extra_info, is_active
            FROM school
            WHERE dean_id = $1 AND is_active = TRUE;
            """,
            dean_id,
        )
        if record is None:
            raise SchoolNotFoundException(parameter="dean_id")
        return record

    @staticmethod
    async def get_all(
        connection: Connection, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT id, name, dean_id, extra_info, is_active
            FROM school
            WHERE is_active = TRUE
            ORDER BY name ASC
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
        name: Optional[str] = None,
        dean_id: Optional[UUID] = None,
        extra_info: Optional[dict] = None,
    ) -> None:
        try:
            response = await connection.execute(
                """--sql
                UPDATE school
                SET name = COALESCE(initcap($2), name),
                    dean_id = COALESCE($3, dean_id),
                    extra_info = COALESCE($4, extra_info)
                WHERE id = $1 AND is_active = TRUE;
                """,
                uid,
                name,
                dean_id,
                extra_info,
            )
            if response != "UPDATE 1":
                raise SchoolNotFoundException(parameter="school_id")
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_school_name":
                    raise SchoolAlreadyExistsException(parameter="name")
                case "uniq_school_dean_id":
                    raise SchoolAlreadyExistsException(parameter="dean_id")
                case _:
                    raise Exception(details)
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            if details["constraint_name"] == "fk_school_dean":
                raise StaffNotFoundException(parameter="dean_id")
            raise Exception(details)

    @staticmethod
    async def delete(connection: Connection, uid: UUID) -> None:
        await connection.execute(
            """--sql
            UPDATE school
            SET is_active = FALSE
            WHERE id = $1;
            """,
            uid,
        )
