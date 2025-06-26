from typing import Any, Optional
from uuid import UUID

from asyncpg import Connection, ForeignKeyViolationError, UniqueViolationError
from cms.departments.exceptions import (
    DepartmentAlreadyExistsException,
    DepartmentNotFoundException,
)
from cms.schools.exceptions import SchoolNotFoundException
from cms.staff.exceptions import StaffNotFoundException
from uuid_utils.compat import uuid7

__all__ = ["DepartmentRepository"]


class DepartmentRepository:
    @staticmethod
    async def create(
        connection: Connection,
        name: str,
        school_id: UUID,
        head_id: UUID,
        extra_info: Optional[dict] = None,
    ) -> UUID:
        uid = uuid7()
        try:
            await connection.execute(
                """
                INSERT INTO department(
                    id, name, school_id, head_id, extra_info
                )
                VALUES($1, initcap($2), $3, $4, $5);
                """,
                uid,
                name,
                school_id,
                head_id,
                extra_info,
            )
            return uid
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_department_name":
                    raise DepartmentAlreadyExistsException(parameter="name")
                case "uniq_department_head_id":
                    raise DepartmentAlreadyExistsException(parameter="head_id")
                case _:
                    raise Exception(details)
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "fk_departments_school_id":
                    raise SchoolNotFoundException(parameter="school_id")
                case "fk_departments_head_id":
                    raise StaffNotFoundException(parameter="head_id")
                case _:
                    raise e

    @staticmethod
    async def exists(connection: Connection, uid: UUID) -> bool:
        result = await connection.fetchval(
            """--sql
            SELECT EXISTS(
                SELECT 1 FROM department WHERE id = $1 AND is_active = TRUE
            );
            """,
            uid,
        )
        return bool(result)

    @staticmethod
    async def get_by_id(connection: Connection, uid: UUID) -> dict[str, Any]:
        record = await connection.fetchrow(
            """--sql
            SELECT id, name, school_id, head_id, extra_info, is_active
            FROM department
            WHERE id = $1 AND is_active = TRUE;
            """,
            uid,
        )
        if record is None:
            raise DepartmentNotFoundException(parameter="id")
        return record

    @staticmethod
    async def get_by_name(connection: Connection, name: str) -> list[dict[str, Any]]:
        name = f"%{name}%"
        record = await connection.fetch(
            """--sql
            SELECT id, name, school_id, head_id, extra_info, is_active
            FROM department
            WHERE name ILIKE $1 AND is_active = TRUE;
            """,
            name,
        )
        return record

    @staticmethod
    async def get_by_school_id(
        connection: Connection, school_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT id, name, school_id, head_id, extra_info, is_active
            FROM department
            WHERE school_id = $1 AND is_active = TRUE
            ORDER BY name ASC
            LIMIT $2 OFFSET $3;
            """,
            school_id,
            limit,
            offset,
        )
        return records

    @staticmethod
    async def get_all(
        connection: Connection, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT id, name, school_id, head_id, extra_info, is_active
            FROM department
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
        school_id: Optional[UUID] = None,
        head_id: Optional[UUID] = None,
        extra_info: Optional[dict] = None,
    ) -> None:
        try:
            response = await connection.execute(
                """--sql
                UPDATE department
                SET name = COALESCE(initcap($2), name),
                    school_id = COALESCE($3, school_id),
                    head_id = COALESCE($4, head_id),
                    extra_info = COALESCE($5, extra_info)
                WHERE id = $1 AND is_active = TRUE;
                """,
                uid,
                name,
                school_id,
                head_id,
                extra_info,
            )
            if response != "UPDATE 1":
                raise DepartmentNotFoundException("id")
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_department_name":
                    raise DepartmentAlreadyExistsException(parameter="name")
                case "uniq_department_head_id":
                    raise DepartmentAlreadyExistsException(parameter="head_id")
                case _:
                    raise Exception(details)
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "fk_departments_school_id":
                    raise SchoolNotFoundException(parameter="school_id")
                case "fk_departments_head_id":
                    raise StaffNotFoundException(parameter="head_id")
                case _:
                    raise Exception(details)

    @staticmethod
    async def delete(connection: Connection, uid: UUID) -> None:
        await connection.execute(
            """--sql
            UPDATE department
            SET is_active = FALSE
            WHERE id = $1 AND is_active = TRUE;
            """,
            uid,
        )

    @staticmethod
    async def get_public_staff(
        connection: Connection, department_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT staff.id, staff.first_name, staff.last_name, users.email_id, users.contact_no,
                staff.position, staff.education, staff.experience, staff.activity,
                staff.other_details, staff.is_public, staff.is_active
            FROM staff
            INNER JOIN users ON staff.id = users.id  AND users.is_active = TRUE
            WHERE staff.id IN (
                SELECT staff_id FROM staff_department WHERE department_id = $1
            ) AND staff.is_active = TRUE AND staff.is_public = TRUE
            ORDER BY last_name ASC, first_name ASC
            LIMIT $2 OFFSET $3;
            """,
            department_id,
            limit,
            offset,
        )
        return records

    @staticmethod
    async def get_staff(
        connection: Connection, department_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT staff.id, staff.first_name, staff.last_name, users.email_id, users.contact_no,
                staff.position, staff.education, staff.experience, staff.activity,
                staff.other_details, staff.is_public, staff.is_active
            FROM staff
            INNER JOIN users ON staff.id = users.id  AND users.is_active = TRUE
            WHERE staff.id IN (
                SELECT staff_id FROM staff_department WHERE department_id = $1
            ) AND staff.is_active = TRUE
            ORDER BY last_name ASC, first_name ASC
            LIMIT $2 OFFSET $3;
            """,
            department_id,
            limit,
            offset,
        )
        return records
