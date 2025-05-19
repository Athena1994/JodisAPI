
from dataclasses import dataclass
from aithena.utils.config_utils import assert_fields_in_dict
from utils.db.db_context import DBContext


@dataclass
class LoggingConfig:
    verbosity: str
    log_path: str
    use_file: bool
    use_stdout: bool
    format: str

    DEFAULT_FMT = "%(asctime)s [%(threadName)-12.12s] " \
                  "[%(levelname)-5.5s]  %(message)s"

    @staticmethod
    def from_dict(d: dict) -> 'LoggingConfig':
        return LoggingConfig(
            verbosity=d.get('verbosity', 'DEBUG'),
            log_path=d.get('log_path', 'logs/'),
            use_file=d.get('use_file', False),
            use_stdout=d.get('use_stdout', True),
            format=d.get('format', LoggingConfig.DEFAULT_FMT)
        )


@dataclass
class ServerModulesConfig:
    path: str

    @staticmethod
    def from_dict(cfg: dict) -> 'ServerModulesConfig':
        return ServerModulesConfig(
            cfg.get('path', 'modules/')
        )


@dataclass
class AppConfig:
    @dataclass
    class Server:
        port: int
        host: str
        root: str

        @staticmethod
        def from_dict(d: dict) -> 'AppConfig.Server':
            return AppConfig.Server(
                root=d.get('root', './'),
                port=d.get('port', 5000),
                host=d.get('host', 'localhost')
            )

    server: Server
    logging: LoggingConfig
    modules: ServerModulesConfig
    db: DBContext.Config


config = None


def get() -> AppConfig:
    return config


def initialize(d: dict, enforce_mandatory_fields: bool = True) -> None:
    global config

    if not enforce_mandatory_fields and 'db' not in d:
        d['db'] = {'user': '', 'password': '', 'host': '', 'db': ''}

    assert_fields_in_dict(d, ['db'])

    config = AppConfig(
        server=AppConfig.Server.from_dict(d.get('server', {})),
        logging=LoggingConfig.from_dict(d.get('logging', {})),
        modules=ServerModulesConfig.from_dict(d.get('modules', {})),
        db=DBContext.Config.from_dict(d['db'])
    )
