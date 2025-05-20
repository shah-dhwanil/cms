from cms.utils.config import Config
from cms.utils.postgres import PgPool
import asyncio


async def test_db_connection():
    await PgPool.initiate()
    conn = await PgPool.get_connection()
    print(await conn.fetch("SELECT 1"))
    await conn.close()
    await PgPool.close()


def main() -> None:
    Config.load_config()
    print(Config.get_config())
    print("Hello from cms!")
    asyncio.run(test_db_connection())
