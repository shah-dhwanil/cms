from json import dumps

from asyncpg import Connection, connect
from cms.permissions.models import ListPermissionResponse
from cms.permissions.repository import PermissionRepository
from cms.users.exceptions import UserAlreadyExistsException
from cms.users.repository import UserRepository
from cms.utils.config import Config
from cms.utils.minio import MinioClient
from miniopy_async.commonconfig import ENABLED
from miniopy_async.versioningconfig import VersioningConfig


async def setup():
    config = Config.get_config()
    connection = await connect(config.POSTGRES_DSN)
    await ensure_default_permissions(connection)
    await ensure_admin_user(connection)
    await ensure_profile_image_bucket()
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


async def ensure_profile_image_bucket():
    async with MinioClient.get_client() as client:
        if not await client.bucket_exists("profile-img"):
            await client.make_bucket("profile-img")
            policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": "*"},
                        "Action": ["s3:GetObject"],
                        "Resource": ["arn:aws:s3:::profile-img/*"],
                    }
                ],
            }
            await client.set_bucket_policy("profile-img", dumps(policy))
            await client.set_bucket_versioning("profile-img", VersioningConfig(ENABLED))
