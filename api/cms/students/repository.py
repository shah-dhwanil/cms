from typing import Any, Optional
from uuid import UUID

from asyncpg import Connection, ForeignKeyViolationError, UniqueViolationError
from cms.users.exceptions import UserDoesNotExists
from cms.students.exceptions import StudentAlreadyExists, StudentDoesNotExists


class StudentRepository:
    @staticmethod
    async def create(
        connection: Connection,
        id: UUID,
        first_name: str,
        last_name: str,
        gender: str,
        aadhaar_no: str,
        apaar_id: str,
    ):
        try:
            await connection.execute(
                """
                INSERT INTO students(id,first_name,last_name,gender,aadhaar_no,apaar_id)
                VALUES($1,$2,$3,$4,$5,$6);
                """,
                id,
                first_name,
                last_name,
                gender,
                aadhaar_no,
                apaar_id,
            )
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "pk_students":
                    raise StudentAlreadyExists(identifier="id")
                case "uniq_students_apaar_id":
                    raise StudentAlreadyExists(identifier="apaar_id")
                case "uniq_students_aadhaar_no":
                    raise StudentAlreadyExists(identifier="aadhaar_no")
                case _:
                    raise StudentAlreadyExists(identifier="unkown")
        except ForeignKeyViolationError:
            raise UserDoesNotExists(identifier="id")

    @staticmethod
    async def get_all(connection: Connection) -> list[dict[str, Any]]:
        result = await connection.fetch(
            """
            SELECT id,first_name,last_name,gender,aadhaar_no,apaar_id,active FROM students WHERE active = TRUE;
            """
        )
        return result

    @staticmethod
    async def get_by_id(connection: Connection, id: UUID) -> dict[str, Any]:
        result = await connection.fetchrow(
            """
            SELECT id,first_name,last_name,gender,aadhaar_no,apaar_id,active FROM students WHERE id=$1;
            """,
            id,
        )
        if result is None:
            raise StudentDoesNotExists(identifier="id")
        return result

    @staticmethod
    async def update(
        connection: Connection,
        id: UUID,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        gender: Optional[str] = None,
        aadhaar_no: Optional[str] = None,
        apaar_id: Optional[str] = None,
    ):
        result = await connection.execute(
            """
            UPDATE students
            SET
                first_name = COALESCE($1,first_name),
                last_name = COALESCE($2,last_name),
                gender = COALESCE($3,gender),
                aadhaar_no = COALESCE($4,aadhaar_no),
                apaar_id = COALESCE($5,apaar_id)
            WHERE id=$6 AND active = TRUE;
            """,
            first_name,
            last_name,
            gender,
            aadhaar_no,
            apaar_id,
            id,
        )
        if result == "UPDATE 0":
            raise StudentDoesNotExists(identifier="id")

    @staticmethod
    async def delete(connection: Connection, id: UUID):
        result = await connection.execute(
            """
            UPDATE students
            SET active = FALSE
            WHERE id=$1;
            """,
            id,
        )
        if result == "UPDATE 0":
            raise StudentDoesNotExists(identifier="id")
