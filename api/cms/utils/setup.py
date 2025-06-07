from asyncpg import Connection, connect
from cms.permissions.repository import PermissionRepository
from cms.permissions.schemas import GetPermissionResponse
from cms.users.repository import UserRepository
from cms.users.exceptions import UserAlreadyExists
from aiofile import async_open
from cms.utils.config import Config
from argon2 import PasswordHasher
from uuid_utils.compat import uuid7


async def setup():
    config = Config.get_config()
    connection = await connect(config.POSTGRES_DSN)
    await setup_permissions(connection)
    await create_admin_user(connection)
    await connection.close()


async def setup_permissions(connection: Connection):
    available_permissions = set(
        map(
            lambda permission: permission["name"],
            await PermissionRepository.get_all(connection),
        )
    )
    async with async_open("./cms/permissions/permissions.json", "r") as fp:
        default_permission = GetPermissionResponse.model_validate_json(await fp.read())
    for i in default_permission.permissions:
        if i.name not in available_permissions:
            await PermissionRepository.create(connection, i.name, i.description)


async def create_admin_user(connection: Connection):
    config = Config.get_config()
    argon2 = PasswordHasher(
        time_cost=config.ARGON_TIME_COST,
        memory_cost=config.ARGON_MEMORY_COST,
        parallelism=config.ARGON_PARALLELISM,
        hash_len=config.ARGON_HASH_LENGTH,
        salt_len=config.ARGON_SALT_LENGTH,
    )
    hashed_password = argon2.hash("Admin@123")
    uid = uuid7()
    try:
        await UserRepository.create(
            connection,
            uid=uid,
            email_id="admin@cms.com",
            contact_no="0000000000",
            password=hashed_password,
            profile_image=uid,
        )
    except UserAlreadyExists:
        result = await UserRepository.get_by_email_id(connection, "admin@cms.com")
        uid = result["id"]

    available_permissions = list(
        map(
            lambda permission: permission["name"],
            await PermissionRepository.get_all(connection),
        )
    )
    await UserRepository.grant_permissions(connection, uid, available_permissions)
