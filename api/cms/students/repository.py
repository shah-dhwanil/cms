from datetime import date
from typing import Any, Optional
from uuid import UUID

from asyncpg import Connection, ForeignKeyViolationError, UniqueViolationError
from cms.students.exceptions import (
    StudentAlreadyExistsException,
    StudentNotFoundException,
)
from cms.users.exceptions import UserNotFoundException

__all__ = ["StudentRepository"]


class StudentRepository:
    @staticmethod
    async def create(
        connection: Connection,
        user_id: UUID,
        first_name: str,
        middle_name: str,
        last_name: str,
        date_of_birth: date,
        gender: str,
        address: str,
        aadhaar_no: str,
        apaar_id: str,
        extra_info: Optional[dict] = None,
    ) -> UUID:
        try:
            await connection.execute(
                """
                INSERT INTO students(
                    id, first_name, middle_name, last_name, date_of_birth, 
                    gender, address, aadhaar_no, apaar_id, extra_info
                )
                VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9, $10);
                """,
                user_id,
                first_name,
                middle_name,
                last_name,
                date_of_birth,
                gender,
                address,
                aadhaar_no,
                apaar_id,
                extra_info,
            )
            return user_id
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_students_aadhaar_no":
                    raise StudentAlreadyExistsException(parameter="aadhaar_no")
                case "uniq_students_apaar_id":
                    raise StudentAlreadyExistsException(parameter="apaar_id")
                case "pk_students":
                    raise StudentAlreadyExistsException(parameter="user_id")
                case _:
                    raise Exception(details)
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            if details["constraint_name"] == "fk_students_user":
                raise UserNotFoundException(parameter="user_id")
            else:
                raise Exception(details)

    @staticmethod
    async def exists(connection: Connection, student_id: UUID) -> bool:
        record = await connection.fetchval(
            """--sql
            SELECT EXISTS(
                SELECT 1 FROM students WHERE id = $1 AND is_active = TRUE
            );
            """,
            student_id,
        )
        return bool(record)

    @staticmethod
    async def get_by_id(connection: Connection, student_id: UUID) -> dict[str, Any]:
        record = await connection.fetchrow(
            """--sql
            SELECT students.id, students.first_name, students.middle_name, students.last_name,
                students.date_of_birth, students.gender, students.address, users.email_id,
                users.contact_no, students.aadhaar_no, students.apaar_id, students.extra_info
            FROM students
            INNER JOIN users ON students.id = users.id AND users.is_active = TRUE
            WHERE students.id = $1 AND students.is_active = TRUE;
            """,
            student_id,
        )
        if record is None:
            raise StudentNotFoundException(parameter="student_id")
        return record

    @staticmethod
    async def get_all(
        connection: Connection, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT students.id, students.first_name, students.middle_name, students.last_name,
                students.date_of_birth, students.gender, students.address, users.email_id,
                users.contact_no, students.aadhaar_no, students.apaar_id, students.extra_info
            FROM students
            INNER JOIN users ON students.id = users.id AND users.is_active = TRUE AND students.is_active = TRUE 
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
        student_id: UUID,
        first_name: Optional[str] = None,
        middle_name: Optional[str] = None,
        last_name: Optional[str] = None,
        date_of_birth: Optional[date] = None,
        gender: Optional[str] = None,
        address: Optional[str] = None,
        aadhaar_no: Optional[str] = None,
        apaar_id: Optional[str] = None,
        extra_info: Optional[dict] = None,
    ) -> None:
        try:
            response = await connection.execute(
                """--sql
                UPDATE students
                SET first_name = COALESCE($2, first_name),
                    middle_name = COALESCE($3, middle_name),
                    last_name = COALESCE($4, last_name),
                    date_of_birth = COALESCE($5, date_of_birth),
                    gender = COALESCE($6, gender),
                    address = COALESCE($7, address),
                    aadhaar_no = COALESCE($8, aadhaar_no),
                    apaar_id = COALESCE($9, apaar_id),
                    extra_info = COALESCE($10, extra_info)
                WHERE id = $1 AND is_active = TRUE;
                """,
                student_id,
                first_name,
                middle_name,
                last_name,
                date_of_birth,
                gender,
                address,
                aadhaar_no,
                apaar_id,
                extra_info,
            )
            if response != "UPDATE 1":
                raise StudentNotFoundException(parameter="student_id")
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_students_aadhaar_no":
                    raise StudentAlreadyExistsException(parameter="aadhaar_no")
                case "uniq_students_apaar_id":
                    raise StudentAlreadyExistsException(parameter="apaar_id")
                case _:
                    raise Exception(details)

    @staticmethod
    async def delete(connection: Connection, student_id: UUID) -> None:
        await connection.execute(
            """--sql
            UPDATE students
            SET
                is_active = FALSE
            WHERE id = $1;
            """,
            student_id,
        )
