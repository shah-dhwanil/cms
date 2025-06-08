from typing import Any, Optional
from uuid import UUID
from asyncpg import Connection, ForeignKeyViolationError, UniqueViolationError
from cms.users.exceptions import UserDoesNotExists
from cms.parents.exceptions import ParentDoesNotExists, ParentAlreadyExists


class ParentRepository:
    @staticmethod
    async def create(
        connection: Connection,
        user_id: UUID,
        father_name: str,
        mother_name: str,
        address: str,
    ):
        try:
            await connection.execute(
                """
                    INSERT INTO parents (id, father_name, mother_name, address)
                    VALUES ($1, $2, $3, $4);
                """,
                user_id,
                father_name,
                mother_name,
                address,
            )
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "pk_parents":
                    raise ParentAlreadyExists(identifier="user_id")
                case _:
                    raise ParentAlreadyExists(identifier="unknown")
        except ForeignKeyViolationError:
            raise UserDoesNotExists(identifier="user_id")

    @staticmethod
    async def get_by_id(connection: Connection, id: UUID) -> dict[str, Any]:
        result = await connection.fetchrow(
            """
            SELECT id, father_name, mother_name, address, active
            FROM parents
            WHERE id = $1;
            """,
            id,
        )
        if result is None:
            raise ParentDoesNotExists(identifier="user_id")
        return result

    @staticmethod
    async def update(
        connection: Connection,
        id: UUID,
        father_name: Optional[str] = None,
        mother_name: Optional[str] = None,
        address: Optional[str] = None,
    ):
        result = await connection.execute(
            """
        UPDATE parents
        SET father_name = COALESCE($1, father_name),
            mother_name = COALESCE($2, mother_name),
            address = COALESCE($3, address)
        WHERE id = $4 AND active = TRUE;
        """,
            father_name,
            mother_name,
            address,
            id,
        )
        if result == "UPDATE 0":
            raise ParentDoesNotExists(identifier="user_id")

    @staticmethod
    async def delete(connection: Connection, id: UUID):
        result = await connection.execute(
            """
            UPDATE parents
            SET active = FALSE
            WHERE id = $1;
            """,
            id,
        )
        if result == "UPDATE 0":
            raise ParentDoesNotExists(identifier="user_id")
