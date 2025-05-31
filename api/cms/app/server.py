import re
from granian.server import Server
from granian.log import LogLevels
from granian.constants import Loops,Interfaces
from cms.utils.config import Config
from pathlib import Path
def start_server():
    Config.load_config()
    config = Config.get_config()
    server = Server(
        target="cms.app.app",
        interface=Interfaces.ASGI,
        address=config.SERVER_HOST,
        port=config.SERVER_PORT,
        reload=True if config.SERVER_ENVIRONMENT == "DEV" else False,
        reload_paths=[Path("./")],
        reload_ignore_paths=[Path("./ logs.json")],
        log_access=True if config.SERVER_ENVIRONMENT == "DEV" else False,
        log_level=LogLevels.debug if config.SERVER_ENVIRONMENT =="DEV" else LogLevels.info,
        loop=Loops.uvloop,
    )
    server.serve()