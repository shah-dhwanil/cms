from contextlib import asynccontextmanager
from cms.utils.config import Config
from cms.utils.postgres import PgPool
from cms.utils.logging import setup_logging
from fastapi import FastAPI


@asynccontextmanager
async def lifespan(app:FastAPI):
    Config.load_config()
    setup_logging()
    await PgPool.initiate()
    yield
    await PgPool.close()