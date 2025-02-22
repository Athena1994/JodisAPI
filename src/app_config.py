
from dataclasses import dataclass
from aithena.utils.config_utils import assert_fields_in_dict

import app_logger
from model.local_model.server_module_manager import ServerModuleManager
from utils.db.db_context import DBContext


@dataclass
class AppConfig:
    @dataclass
    class Server:
        port: int
        root: str

        @staticmethod
        def from_dict(d: dict) -> 'AppConfig.Server':
            return AppConfig.Server(
                port=d.get('port', 5000),
                root=d.get('root', './')
            )

    server: Server
    logging: app_logger.Config
    modules: ServerModuleManager.Config
    db: DBContext.Config

    @staticmethod
    def from_dict(d: dict) -> 'AppConfig':
        assert_fields_in_dict(d, ['modules', 'db'])
        return AppConfig(
            server=AppConfig.Server.from_dict(d.get('server', {})),
            logging=app_logger.Config.from_dict(d.get('logging', {})),
            modules=ServerModuleManager.Config.from_dict(d['modules']),
            db=DBContext.Config.from_dict(d['db'])
        )
