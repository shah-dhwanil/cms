from typing import ClassVar, Optional
from asyncpg import Pool, create_pool, Connection
from .config import Config


class PgPool:
    pool: ClassVar[Optional[Pool]] = None

    @classmethod
    async def initiate(cls) -> None:
        if cls.pool is not None:
            return
        config = Config.get_config()
        cls.pool = await create_pool(
            dsn=config.POSTGRES_DSN,
            min_size=config.POSTGRES_MIN_CONNECTIONS,
            max_size=config.POSTGRES_MAX_CONNECTIONS,
        )

    @classmethod
    async def get_connection(cls) -> Connection:
        if cls.pool is None:
            raise Exception("Pool not initiated")
        return await cls.pool.acquire()

    @classmethod
    async def close(cls):
        if cls.pool is None:
            return
        await cls.pool.close()
