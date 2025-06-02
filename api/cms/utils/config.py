from typing import Self
from pydantic import BaseModel
from dotenv import load_dotenv
from tomllib import load
from os import environ

__config__ = None


class Config(BaseModel):
    SERVER_ENVIRONMENT: str
    SERVER_HOST: str
    SERVER_PORT: int
    POSTGRES_DSN: str
    POSTGRES_MIN_CONNECTIONS: int
    POSTGRES_MAX_CONNECTIONS: int
    MINIO_ADDRESS: str
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE:bool
    @classmethod
    def load_config(cls):
        load_dotenv("./.env")
        environment = environ.get("CMS_SERVER_ENVIRONMENT", None)
        if environment is None:
            raise ValueError("Server Environment must be set in the system")
        load_dotenv(f".env.{environment.lower()}")
        config = dict()
        with open("./config.toml", "rb") as f:
            toml_config = load(f)
            config.update(toml_config.get("DEFAULT", dict()))
            config.update(toml_config.get(environment, dict()))
        for key in environ:
            if key.startswith("CMS_"):
                config[key.removeprefix("CMS_")] = environ[key]
        global __config__
        __config__ = cls(**config)

    @classmethod
    def get_config(cls) -> Self:
        global __config__
        if __config__ is None:
            raise Exception("Config is not loaded")
        return __config__
