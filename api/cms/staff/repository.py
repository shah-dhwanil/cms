from typing import Any, Dict, Optional
from uuid import UUID

from asyncpg import Connection, ForeignKeyViolationError, UniqueViolationError
from cms.departments.exceptions import DepartmentNotFoundException
from cms.staff.exceptions import StaffAlreadyExistsException, StaffNotFoundException
from cms.users.exceptions import UserNotFoundException
from cms.users.repository import UserRepository

__all__ = ["StaffRepository"]


class StaffRepository:
    @staticmethod
    async def create(
        connection: Connection,
        user_id: UUID,
        first_name: str,
        last_name: str,
        position: str,
        education: Dict[str, Any],
        experience: Dict[str, Any],
        activity: Dict[str, Any],
        other_details: Optional[Dict[str, Any]] = None,
        is_public: bool = True,
    ) -> UUID:
        try:
            await connection.execute(
                """
                INSERT INTO staff(
                    id, first_name, last_name, position, education, 
                    experience, activity, other_details, is_public
                )
                VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9)
                RETURNING id;
                """,
                user_id,
                first_name,
                last_name,
                position,
                education,
                experience,
                activity,
                other_details,
                is_public,
            )
            return user_id
        except ForeignKeyViolationError as e:
            defails = e.as_dict()
            if defails["constraint_name"] == "fk_staff_users":
                raise UserNotFoundException(parameter="user_id")
            else:
                raise e
        except UniqueViolationError as e:
            details = e.as_dict()
            if details["constraint_name"] == "pk_staff":
                raise StaffAlreadyExistsException(parameter="user_id")
            else:
                raise e

    @staticmethod
    async def exists(connection: Connection, staff_id: UUID) -> bool:
        result = await connection.fetchval(
            """--sql
            SELECT EXISTS(
                SELECT 1 FROM staff WHERE id = $1 AND is_active = TRUE
            );
            """,
            staff_id,
        )
        return bool(result)

    @staticmethod
    async def get_by_id(connection: Connection, staff_id: UUID) -> dict[str, Any]:
        record = await connection.fetchrow(
            """--sql
            SELECT staff.id, staff.first_name, staff.last_name, users.email_id, users.contact_no,
                staff.position, staff.education, staff.experience, staff.activity,
                staff.other_details, staff.is_public, staff.is_active
            FROM staff
            INNER JOIN users ON staff.id = users.id  AND users.is_active = TRUE
            WHERE staff.id = $1 AND staff.is_active = TRUE;
            """,
            staff_id,
        )
        if record is None:
            raise StaffNotFoundException(parameter="staff_id")
        return record

    @staticmethod
    async def get_all_public_staff(
        connection: Connection, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT staff.id, staff.first_name, staff.last_name, users.email_id, users.contact_no,
                staff.position, staff.education, staff.experience, staff.activity,
                staff.other_details, staff.is_public, staff.is_active
            FROM staff
            INNER JOIN users ON staff.id = users.id  AND users.is_active = TRUE
            WHERE staff.is_active = TRUE AND staff.is_public = TRUE
            ORDER BY last_name ASC, first_name ASC
            LIMIT $1 OFFSET $2;
            """,
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
            SELECT staff.id, staff.first_name, staff.last_name, users.email_id, users.contact_no,
                staff.position, staff.education, staff.experience, staff.activity,
                staff.other_details, staff.is_public, staff.is_active
            FROM staff
            INNER JOIN users ON staff.id = users.id  AND users.is_active = TRUE
            WHERE staff.is_active = TRUE
            ORDER BY last_name ASC, first_name ASC
            LIMIT $1 OFFSET $2;
            """,
            limit,
            offset,
        )
        return records

    @staticmethod
    async def update(
        connection: Connection,
        staff_id: UUID,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        position: Optional[str] = None,
        education: Optional[Dict[str, Any]] = None,
        experience: Optional[Dict[str, Any]] = None,
        activity: Optional[Dict[str, Any]] = None,
        other_details: Optional[Dict[str, Any]] = None,
        is_public: Optional[bool] = None,
    ) -> None:
        response = await connection.execute(
            """--sql
            UPDATE staff
            SET first_name = COALESCE($2, first_name),
                last_name = COALESCE($3, last_name),
                position = COALESCE($4, position),
                education = COALESCE($5, education),
                experience = COALESCE($6, experience),
                activity = COALESCE($7, activity),
                other_details = COALESCE($8, other_details),
                is_public = COALESCE($9, is_public)
            WHERE id = $1 AND is_active = TRUE;
            """,
            staff_id,
            first_name,
            last_name,
            position,
            education,
            experience,
            activity,
            other_details,
            is_public,
        )
        if response != "UPDATE 1":
            raise StaffNotFoundException("staff_id")

    @staticmethod
    async def delete(connection: Connection, staff_id: UUID) -> None:
        # await connection.execute(
        #     """--sql
        #     UPDATE staff
        #     SET is_active = FALSE
        #     WHERE id = $1;
        #     """,
        #     staff_id,
        # )
        await UserRepository.delete(connection, staff_id)

    @staticmethod
    async def link_department(
        connection: Connection, staff_id: UUID, department_id: UUID
    ) -> None:
        try:
            await connection.execute(
                """--sql
                INSERT INTO staff_department(staff_id, department_id)
                VALUES($1, $2)
                ON CONFLICT (staff_id) DO UPDATE SET department_id = EXCLUDED.department_id;
                """,
                staff_id,
                department_id,
            )
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            if details["constraint_name"] == "fk_staff_department_staff":
                raise StaffNotFoundException(parameter="staff_id")
            elif details["constraint_name"] == "fk_staff_department_department":
                raise DepartmentNotFoundException(parameter="department_id")
            else:
                raise e

    @staticmethod
    async def unlink_department(connection: Connection, staff_id: UUID) -> None:
        await connection.execute(
            """--sql
            DELETE FROM staff_department
            WHERE staff_id = $1;
            """,
            staff_id,
        )

    @staticmethod
    async def get_department(
        connection: Connection, staff_id: UUID
    ) -> Optional[dict[str, Any]]:
        department = await connection.fetchrow(
            """--sql
            SELECT department.id, department.name FROM staff_department
            INNER JOIN department ON staff_department.department_id = department.id AND department.is_active = TRUE
            WHERE staff_id = $1;
            """,
            staff_id,
        )
        return department
