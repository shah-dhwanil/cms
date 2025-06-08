from typing import Any, Optional
from asyncpg import Connection, ForeignKeyViolationError, UniqueViolationError
from uuid import UUID
from cms.staff.exceptions import StaffAlreadyExists, StaffDoesNotExists
from cms.users.exceptions import UserDoesNotExists


class StaffRepository:
    @staticmethod
    async def create(
        connection: Connection,
        id: UUID,
        first_name: str,
        last_name: str,
        position: str,
        education: dict[str, Any],
        experience: dict[str, Any],
        activity: dict[str, Any],
        other_details: Optional[dict[str, Any]] = None,
        public: bool = True,
    ):
        try:
            await connection.execute(
                """
                INSERT INTO staff(
                    id,
                    first_name,
                    last_name,
                    position,
                    education,
                    experience,
                    activity,
                    other_details,
                    public
                )
                VALUES($1,$2,$3,$4,$5,$6,$7,$8,$9);
                """,
                id,
                first_name,
                last_name,
                position,
                education,
                experience,
                activity,
                other_details,
                public,
            )
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "pk_staff":
                    raise StaffAlreadyExists(identifier="id")
                case _:
                    raise StaffAlreadyExists(identifier="unkown")
        except ForeignKeyViolationError:
            raise UserDoesNotExists(identifier="id")

    @staticmethod
    async def get_all(connection: Connection) -> list[dict[str, Any]]:
        result = await connection.fetch(
            """
            SELECT
                id,
                first_name,
                last_name,
                position,
                education,
                experience,
                activity,
                other_details,
                public,
                active
            FROM staff WHERE active = TRUE;
            """
        )
        return result

    @staticmethod
    async def get_by_id(connection: Connection, id: UUID) -> dict[str, Any]:
        result = await connection.fetchrow(
            """
            SELECT
                id,
                first_name,
                last_name,
                position,
                education,
                experience,
                activity,
                other_details,
                public,
                active
            FROM staff WHERE id=$1;
            """,
            id,
        )
        if result is None:
            raise StaffDoesNotExists(identifier="id")
        return result

    @staticmethod
    async def update(
        connection: Connection,
        id: UUID,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        position: Optional[str] = None,
        education: Optional[dict[str, Any]] = None,
        experience: Optional[dict[str, Any]] = None,
        activity: Optional[dict[str, Any]] = None,
        other_details: Optional[dict[str, Any]] = None,
        public: Optional[bool] = None,
    ):
        result = await connection.execute(
            """
            UPDATE staff
            SET
                first_name = COALESCE($1,first_name),
                last_name = COALESCE($2,last_name),
                position = COALESCE($3,position),
                education = COALESCE($4,education),
                experience = COALESCE($5,experience),
                activity = COALESCE($6,activity),
                other_details = COALESCE($7,other_details),
                public = COALESCE($8,public)
            WHERE id=$9 AND active = TRUE;        
            """,
            first_name,
            last_name,
            position,
            education,
            experience,
            activity,
            other_details,
            public,
            id,
        )
        if result == "UPDATE 0":
            raise StaffDoesNotExists(identifier="id")

    @staticmethod
    async def delete(connection: Connection, id: UUID):
        result = await connection.execute(
            """
            UPDATE staff
            SET active = FALSE
            WHERE id=$1;
            """,
            id,
        )
        if result == "UPDATE 0":
            raise StaffDoesNotExists(identifier="id")
