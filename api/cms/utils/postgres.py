from typing import ClassVar, Optional
from asyncpg import Pool, create_pool
from .config import Config
from json import loads, dumps


class PgPool:
    pool: ClassVar[Optional[Pool]] = None

    @classmethod
    async def initiate(cls) -> None:
        if cls.pool is not None:
            return
        config = Config.get_config()

        async def init_connection(conn):
            await conn.set_type_codec(
                "json",
                encoder=dumps,
                decoder=loads,
                schema="pg_catalog",
            )

        cls.pool = await create_pool(
            dsn=config.POSTGRES_DSN,
            min_size=config.POSTGRES_MIN_CONNECTIONS,
            max_size=config.POSTGRES_MAX_CONNECTIONS,
            init=init_connection,
        )

    @classmethod
    async def get_connection(cls):
        if cls.pool is None:
            raise Exception("Pool not initiated")
        client = await cls.pool.acquire()
        yield client
        await cls.pool.release(client)

    @classmethod
    async def close(cls):
        if cls.pool is None:
            return
        await cls.pool.close()
