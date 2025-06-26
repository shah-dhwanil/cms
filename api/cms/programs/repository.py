from typing import Any, Optional
from uuid import UUID

from asyncpg import Connection, ForeignKeyViolationError, UniqueViolationError
from cms.departments.exceptions import DepartmentNotFoundException
from cms.programs.exceptions import (
    ProgramAlreadyExistsException,
    ProgramNotFoundException,
)
from uuid_utils.compat import uuid7

# filepath: /workspaces/cms/api/cms/programs/repository.py


__all__ = ["ProgramRepository"]


class ProgramRepository:
    @staticmethod
    async def create(
        connection: Connection,
        name: str,
        degree_name: str,
        degree_type: str,
        offered_by: UUID,
        extra_info: Optional[dict] = None,
    ) -> UUID:
        uid = uuid7()
        try:
            await connection.execute(
                """
                INSERT INTO programs(
                    id, name, degree_name, degree_type, offered_by, extra_info
                )
                VALUES($1, $2, $3, $4, $5, $6);
                """,
                uid,
                name,
                degree_name,
                degree_type,
                offered_by,
                extra_info,
            )
            return uid
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_programs_name":
                    raise ProgramAlreadyExistsException(parameter="name")
                case _:
                    raise Exception(details)
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "fk_programs_departments":
                    raise DepartmentNotFoundException(parameter="offered_by")
                case _:
                    raise Exception(details)

    @staticmethod
    async def exists(connection: Connection, uid: UUID) -> bool:
        result = await connection.fetchval(
            """--sql
            SELECT EXISTS(
                SELECT 1 FROM programs WHERE id = $1 AND is_active = TRUE
            );
            """,
            uid,
        )
        return bool(result)

    @staticmethod
    async def get_by_id(connection: Connection, uid: UUID) -> dict[str, Any]:
        record = await connection.fetchrow(
            """--sql
            SELECT programs.id, programs.name, programs.degree_name, programs.degree_type, departments.id as department_id, departments.name as department_name, programs.extra_info
            FROM programs
            INNER JOIN departments ON programs.offered_by = departments.id
            WHERE programs.id = $1 AND programs.is_active = TRUE;
            """,
            uid,
        )
        if record is None:
            raise ProgramNotFoundException(parameter="program_id")
        return record

    @staticmethod
    async def search_by_name(connection: Connection, name: str) -> list[dict[str, Any]]:
        name = f"%{name}%"
        record = await connection.fetch(
            """--sql
            SELECT programs.id, programs.name, programs.degree_name, programs.degree_type, departments.id as department_id, departments.name as department_name, programs.extra_info
            FROM programs
            INNER JOIN departments ON programs.offered_by = departments.id
            WHERE programs.name ILIKE $1 AND programs.is_active = TRUE;
            """,
            name,
        )
        if record is None:
            raise ProgramNotFoundException(parameter="name")
        return record

    @staticmethod
    async def get_all(
        connection: Connection, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT programs.id, programs.name, programs.degree_name, programs.degree_type, departments.id as department_id, departments.name as department_name, programs.extra_info
            FROM programs
            INNER JOIN departments ON programs.offered_by = departments.id
            WHERE programs.is_active = TRUE
            ORDER BY name ASC
            LIMIT $1 OFFSET $2;
            """,
            limit,
            offset,
        )
        return records

    @staticmethod
    async def get_by_department(
        connection: Connection, department_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT programs.id, programs.name, programs.degree_name, programs.degree_type, departments.id as department_id, departments.name as department_name, programs.extra_info
            FROM programs
            INNER JOIN departments ON programs.offered_by = departments.id
            WHERE programs.offered_by = $1 AND programs.is_active = TRUE
            ORDER BY name ASC
            LIMIT $2 OFFSET $3;
            """,
            department_id,
            limit,
            offset,
        )
        return records

    @staticmethod
    async def get_by_school(
        connection: Connection, school_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT programs.id, programs.name, programs.degree_name, programs.degree_type, departments.id as department_id, departments.name as department_name, programs.extra_info
            FROM programs 
            JOIN departments ON programs.offered_by = departments.id
            WHERE departments.school_id = $1 AND programs.is_active = TRUE
            ORDER BY programs.name ASC
            LIMIT $2 OFFSET $3;
            """,
            school_id,
            limit,
            offset,
        )
        return records

    @staticmethod
    async def update(
        connection: Connection,
        uid: UUID,
        name: Optional[str] = None,
        degree_name: Optional[str] = None,
        degree_type: Optional[str] = None,
        offered_by: Optional[UUID] = None,
        extra_info: Optional[dict] = None,
    ) -> None:
        try:
            response = await connection.execute(
                """--sql
                UPDATE programs
                SET name = COALESCE($2, name),
                    degree_name = COALESCE($3, degree_name),
                    degree_type = COALESCE($4, degree_type),
                    offered_by = COALESCE($5, offered_by),
                    extra_info = COALESCE($6, extra_info)
                WHERE id = $1 AND is_active = TRUE;
                """,
                uid,
                name,
                degree_name,
                degree_type,
                offered_by,
                extra_info,
            )
            if response != "UPDATE 1":
                raise ProgramNotFoundException("program_id")
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "fk_programs_departments":
                    raise DepartmentNotFoundException(parameter="offered_by")
                case _:
                    raise Exception(details)
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_programs_name":
                    raise ProgramAlreadyExistsException(parameter="name")
                case _:
                    raise Exception(details)

    @staticmethod
    async def delete(connection: Connection, uid: UUID) -> None:
        response = await connection.execute(
            """--sql
            UPDATE programs
            SET is_active = FALSE
            WHERE id = $1;
            """,
            uid,
        )
        if response != "UPDATE 1":
            raise ProgramNotFoundException("program_id")
