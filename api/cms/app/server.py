from granian.server import Server
from granian.log import LogLevels
from granian.constants import Loops, Interfaces
from cms.utils.config import Config
from cms.utils.setup import setup
from pathlib import Path
from uvloop import run


def start_server():
    Config.load_config()
    config = Config.get_config()
    run(setup())
    server = Server(
        target="cms.app.app",
        interface=Interfaces.ASGI,
        address=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=True if config.SERVER_ENVIRONMENT == "DEV" else False,
        reload_paths=[Path("./cms")],
        log_access=True if config.SERVER_ENVIRONMENT == "DEV" else False,
        log_level=LogLevels.debug
        if config.SERVER_ENVIRONMENT == "DEV"
        else LogLevels.info,
        loop=Loops.uvloop,
    )
    server.serve()
