from asyncpg import connect, Connection
from cms.permissions.models import ListPermissionResponse
from cms.permissions.repository import PermissionRepository
from cms.users.exceptions import UserAlreadyExistsException
from cms.users.repository import UserRepository
from cms.utils.config import Config


async def setup():
    config = Config.get_config()
    connection = await connect(config.POSTGRES_DSN)
    await ensure_default_permissions(connection)
    await ensure_admin_user(connection)
    await connection.close()


async def ensure_default_permissions(connection: Connection):
    available_permissions = set(
        map(
            lambda permission: permission["slug"],
            await PermissionRepository.get_all(connection),
        )
    )
    with open("./permissions.json", "r") as fp:
        default_permission = ListPermissionResponse.model_validate_json(fp.read())
    for i in default_permission.permissions:
        if i.slug not in available_permissions:
            await PermissionRepository.create(connection, i.slug, i.description)


async def ensure_admin_user(connection: Connection):
    from cms.utils.argon2 import hash_password

    try:
        uid = await UserRepository.create(
            connection,
            email_id="admin@cms.com",
            password=hash_password("Admin@123"),
            contact_no="+91 98746 54321",
        )
    except UserAlreadyExistsException:
        user = await UserRepository.get_by_email_id(connection, "admin@cms.com")
        uid = user["id"]
    permissions = await PermissionRepository.get_all(connection, limit=1000, offset=0)
    perms = [perm["slug"] for perm in permissions]
    await UserRepository.grant_permissions(
        connection, uid, perms
    )  # Grant all permissions to admin user
