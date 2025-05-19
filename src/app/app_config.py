
from pathlib import Path

from jodisutils.config.helper import load_config
from jodisutils.db.db_context import DBContext
from jodisutils.config.decorator import config as configdecorator
from jodisutils.config.attribute import Attribute

DEFAULT_FMT = "%(asctime)s [%(threadName)-12.12s] " \
                "[%(levelname)-5.5s]  %(message)s"


@configdecorator
class LoggingConfig:
    verbosity: str = Attribute(default='DEBUG')
    log_path: str = Attribute(default='logs/')
    use_file: bool = Attribute(default=False)
    use_stdout: bool = Attribute(default=True)
    format: str = Attribute(default=DEFAULT_FMT)


@configdecorator
class ServerModulesConfig:
    path: str = Attribute(default='modules/')


@configdecorator
class AppConfig:
    @configdecorator
    class Server:
        port: int = Attribute(default=5000)
        host: str = Attribute(default='localhost')
        root: str = Attribute(default='./')

    server: Server = Attribute(default={})
    logging: LoggingConfig = Attribute(default={})
    modules: ServerModulesConfig = Attribute(default={})
    db: DBContext.Config = Attribute(default={}, required=True)


config = None


def get() -> AppConfig:
    return config


def initialize(path: Path) -> None:
    global config

    config = load_config(path, AppConfig)
