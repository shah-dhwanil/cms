from typing import Any, Optional
from uuid import UUID
from asyncpg import Connection, ForeignKeyViolationError, UniqueViolationError
from cms.users.exceptions import UserNotFoundException


from cms.parents.exceptions import (
    ParentAlreadyExistsException,
    ParentNotFoundException,
)
from cms.users.repository import UserRepository

__all__ = ["ParentRepository"]


class ParentRepository:
    @staticmethod
    async def create(
        connection: Connection,
        user_id: UUID,
        fathers_name: str,
        mothers_name: str,
        fathers_email_id: str,
        mothers_email_id: str,
        fathers_contact_no: str,
        mothers_contact_no: str,
        address: str,
        extra_info: Optional[dict] = None,
    ) -> UUID:
        try:
            await connection.execute(
                """
                INSERT INTO parents(
                    id, fathers_name, mothers_name, fathers_email_id, mothers_email_id, 
                    fathers_contact_no, mothers_contact_no, address, extra_info
                )
                VALUES($1, $2, $3, $4, $5, $6, $7, $8, $9);
                """,
                user_id,
                fathers_name,
                mothers_name,
                fathers_email_id,
                mothers_email_id,
                fathers_contact_no,
                mothers_contact_no,
                address,
                extra_info,
            )
            return user_id
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_fathers_email_id":
                    raise ParentAlreadyExistsException(parameter="fathers_email_id")
                case "uniq_mothers_email_id":
                    raise ParentAlreadyExistsException(parameter="mothers_email_id")
                case "uniq_fathers_contact_no":
                    raise ParentAlreadyExistsException(parameter="fathers_contact_no")
                case "uniq_mothers_contact_no":
                    raise ParentAlreadyExistsException(parameter="mothers_contact_no")
                case "pk_parents":
                    raise ParentAlreadyExistsException(parameter="user_id")
                case _:
                    raise Exception(details)
        except ForeignKeyViolationError as e:
            details = e.as_dict()
            if details["constraint_name"] == "fk_parents_users":
                raise UserNotFoundException(parameter="user_id")
            else:
                raise Exception(details)

    @staticmethod
    async def exists(connection: Connection, parent_id: UUID) -> bool:
        record = await connection.fetchval(
            """--sql
            SELECT EXISTS(
                SELECT 1 FROM parents WHERE id = $1 AND is_active = TRUE
            );
            """,
            parent_id,
        )
        return bool(record)

    @staticmethod
    async def get_by_id(connection: Connection, parent_id: UUID) -> dict[str, Any]:
        record = await connection.fetchrow(
            """--sql
            SELECT parents.id, parents.fathers_name, parents.mothers_name, 
                parents.fathers_email_id, parents.mothers_email_id, 
                parents.fathers_contact_no, parents.mothers_contact_no, 
                parents.address, parents.extra_info
            FROM parents
            WHERE parents.id = $1 AND parents.is_active = TRUE;
            """,
            parent_id,
        )
        if record is None:
            raise ParentNotFoundException(parameter="parent_id")
        return record

    @staticmethod
    async def get_all(
        connection: Connection, limit: int = 100, offset: int = 0
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT parents.id, parents.fathers_name, parents.mothers_name, 
                parents.fathers_email_id, parents.mothers_email_id, 
                parents.fathers_contact_no, parents.mothers_contact_no, 
                parents.address, parents.extra_info
            FROM parents
            WHERE parents.is_active = TRUE
            ORDER BY parents.fathers_name ASC
            LIMIT $1 OFFSET $2;
            """,
            limit,
            offset,
        )
        return records

    @staticmethod
    async def update(
        connection: Connection,
        parent_id: UUID,
        fathers_name: Optional[str] = None,
        mothers_name: Optional[str] = None,
        fathers_email_id: Optional[str] = None,
        mothers_email_id: Optional[str] = None,
        fathers_contact_no: Optional[str] = None,
        mothers_contact_no: Optional[str] = None,
        address: Optional[str] = None,
        extra_info: Optional[dict] = None,
    ) -> None:
        try:
            response = await connection.execute(
                """--sql
                UPDATE parents
                SET fathers_name = COALESCE($2, fathers_name),
                    mothers_name = COALESCE($3, mothers_name),
                    fathers_email_id = COALESCE($4, fathers_email_id),
                    mothers_email_id = COALESCE($5, mothers_email_id),
                    fathers_contact_no = COALESCE($6, fathers_contact_no),
                    mothers_contact_no = COALESCE($7, mothers_contact_no),
                    address = COALESCE($8, address),
                    extra_info = COALESCE($9, extra_info)
                WHERE id = $1 AND is_active = TRUE;
                """,
                parent_id,
                fathers_name,
                mothers_name,
                fathers_email_id,
                mothers_email_id,
                fathers_contact_no,
                mothers_contact_no,
                address,
                extra_info,
            )
            if response != "UPDATE 1":
                raise ParentNotFoundException(parameter="parent_id")
        except UniqueViolationError as e:
            details = e.as_dict()
            match details["constraint_name"]:
                case "uniq_fathers_email_id":
                    raise ParentAlreadyExistsException(parameter="fathers_email_id")
                case "uniq_mothers_email_id":
                    raise ParentAlreadyExistsException(parameter="mothers_email_id")
                case "uniq_fathers_contact_no":
                    raise ParentAlreadyExistsException(parameter="fathers_contact_no")
                case "uniq_mothers_contact_no":
                    raise ParentAlreadyExistsException(parameter="mothers_contact_no")
                case _:
                    raise Exception(details)

    @staticmethod
    async def delete(connection: Connection, parent_id: UUID) -> None:
        # await connection.execute(
        #     """--sql
        #     UPDATE parents
        #     SET
        #         is_active = FALSE
        #     WHERE id = $1;
        #     """,
        #     parent_id,
        # )
        await UserRepository.delete(connection, parent_id)

    @staticmethod
    async def get_students(
        connection: Connection, parent_id: UUID
    ) -> list[dict[str, Any]]:
        records = await connection.fetch(
            """--sql
            SELECT students.id, students.first_name, students.middle_name, students.last_name,
                students.date_of_birth, students.gender, students.address, users.email_id,
                users.contact_no, students.aadhaar_no, students.apaar_id, students.extra_info
            FROM students
            INNER JOIN users ON students.id = users.id AND users.is_active = TRUE AND students.is_active = TRUE 
            WHERE students.id IN (
                SELECT student_id FROM student_parent WHERE parent_id = $1
            );
            """,
            parent_id,
        )
        return records
