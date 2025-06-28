from typing import Any, Optional
from uuid import UUID

from asyncpg import Connection, ForeignKeyViolationError, UniqueViolationError

# filepath: /workspaces/cms/api/cms/batch/repository.py
from cms.batch.exceptions import (
    BatchAlreadyExistsException,
    BatchNotFoundException,
)
from cms.programs.exceptions import ProgramNotFoundException
from uuid_utils.compat import uuid7

__all__ = ["BatchRepository"]


class BatchRepository:
    @staticmethod
    async def create(
        connection: Connection,
        code: str,
        program_id: UUID,
        name: str,
        year: int,
        extra_info: Optional[dict] = None,
    ) -> UUID:
        uid = uuid7()
        try:
            await connection.execute(
                """
                INSERT INTO batch(
                    id, code, program_id, name, year, extra_info
                )
                VALUES($1, $2, $3, $4, $5, $6);
                """,
                uid,
                code,
                program_id,
                name,
                year,
                extra_info,
            )
            return uid
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_batch_code":
                    raise BatchAlreadyExistsException(parameter="code")
                case "uniq_batch_name":
                    raise BatchAlreadyExistsException(parameter="program+year+name")
                case _:
                    raise Exception(details)
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "fk_batch_program":
                    raise ProgramNotFoundException(parameter="program_id")
                case _:
                    raise e

    @staticmethod
    async def exists(connection: Connection, uid: UUID) -> bool:
        result = await connection.fetchval(
            """--sql
            SELECT EXISTS(
                SELECT 1 FROM batch WHERE id = $1 AND is_active = TRUE
            );
            """,
            uid,
        )
        return bool(result)

    @staticmethod
    async def get_by_id(connection: Connection, uid: UUID) -> dict[str, Any]:
        record = await connection.fetchrow(
            """--sql
            SELECT batch.id, batch.code, batch.program_id, programs.name as program_name, batch.name, batch.year, batch.extra_info
            FROM batch
            INNER JOIN programs ON batch.program_id = programs.id
            WHERE batch.id = $1 AND batch.is_active = TRUE;
            """,
            uid,
        )
        if record is None:
            raise BatchNotFoundException(parameter="id")
        return record

    @staticmethod
    async def get_by_code(connection: Connection, code: str) -> dict[str, Any]:
        record = await connection.fetchrow(
            """--sql
            SELECT batch.id, batch.code, batch.program_id, programs.name as program_name, batch.name, batch.year, batch.extra_info
            FROM batch
            INNER JOIN programs ON batch.program_id = programs.id
            WHERE batch.code = $1 AND batch.is_active = TRUE;
            """,
            code,
        )
        if record is None:
            raise BatchNotFoundException(parameter="code")
        return record

    @staticmethod
    async def get_by_program_id(
        connection: Connection, program_id: UUID, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT batch.id, batch.code, batch.program_id, programs.name as program_name, batch.name, batch.year, batch.extra_info
            FROM batch
            INNER JOIN programs ON batch.program_id = programs.id
            WHERE batch.program_id = $1 AND batch.is_active = TRUE
            ORDER BY batch.year DESC, programs.name ASC, batch.name ASC
            LIMIT $2 OFFSET $3;
            """,
            program_id,
            limit,
            offset,
        )
        return records

    @staticmethod
    async def get_by_year_program_id(
        connection: Connection, program_id: UUID, year: int
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT batch.id, batch.code, batch.program_id, programs.name as program_name, batch.name, batch.year, batch.extra_info
            FROM batch
            INNER JOIN programs ON batch.program_id = programs.id
            WHERE batch.program_id = $1 AND batch.year = $2 AND batch.is_active = TRUE
            ORDER BY batch.year DESC, programs.name ASC, batch.name ASC;
            """,
            program_id,
            year,
        )
        return records

    @staticmethod
    async def get_by_year(connection: Connection, year: int) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT batch.id, batch.code, batch.program_id, programs.name as program_name, batch.name, batch.year, batch.extra_info
            FROM batch
            INNER JOIN programs ON batch.program_id = programs.id
            WHERE batch.year = $1 AND batch.is_active = TRUE
            ORDER BY batch.year DESC, programs.name ASC, batch.name ASC;
            """,
            year,
        )
        return records

    @staticmethod
    async def get_all(
        connection: Connection, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT batch.id, batch.code, batch.program_id, programs.name as program_name, batch.name, batch.year, batch.extra_info
            FROM batch
            INNER JOIN programs ON batch.program_id = programs.id
            WHERE batch.is_active = TRUE
            ORDER BY batch.year DESC, programs.name ASC, batch.name ASC
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
        code: Optional[str] = None,
        program_id: Optional[UUID] = None,
        name: Optional[str] = None,
        year: Optional[int] = None,
        extra_info: Optional[dict] = None,
    ) -> None:
        try:
            response = await connection.execute(
                """--sql
                UPDATE batch
                SET code = COALESCE($2, code),
                    program_id = COALESCE($3, program_id),
                    name = COALESCE($4, name),
                    year = COALESCE($5, year),
                    extra_info = COALESCE($6, extra_info)
                WHERE id = $1 AND is_active = TRUE;
                """,
                uid,
                code,
                program_id,
                name,
                year,
                extra_info,
            )
            if response != "UPDATE 1":
                raise BatchNotFoundException("id")
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_batch_code":
                    raise BatchAlreadyExistsException(parameter="code")
                case "uniq_batch_name":
                    raise BatchAlreadyExistsException(parameter="name")
                case _:
                    raise Exception(details)
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "fk_batch_program":
                    raise ProgramNotFoundException(parameter="program_id")
                case _:
                    raise Exception(details)

    @staticmethod
    async def delete(connection: Connection, uid: UUID) -> None:
        await connection.execute(
            """--sql
            UPDATE batch
            SET is_active = FALSE
            WHERE id = $1 AND is_active = TRUE;
            """,
            uid,
        )
