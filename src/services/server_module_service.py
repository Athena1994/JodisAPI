

import logging
import os
import app_constants
from model.exeptions import StateError
from model.local_model.server_module_manager import ServerModuleManager
from utils import path_builder
from utils.model_managing.subject_session import SubjectSession


class ServerModuleService:

    def __init__(self):
        self._version = '0.0.1'

    def get_version(self):
        return self._version

    def get_modules(self):
        return ['module1', 'module2', 'module3']

    def register_module(self, module_name):
        return f"Module {module_name} registered!"

    """Detect all modules in the module path and register them. Creates the
    module path if it does not exist."""
    @staticmethod
    def examine_modules(session: SubjectSession) -> None:

        # assert all modules have stopped
        for m in ServerModuleManager.all(session):
            if ServerModuleManager(session, m.name).is_running():
                raise StateError(f"Module '{m.name}' is still running!")

        modules_path = path_builder.build_path('', app_constants.MODULE_DOMAIN)

        # create module path if it does not exist
        if not os.path.exists(modules_path):
            os.makedirs(modules_path)

        # find all modules in module path
        detected_modules = set(os.listdir(modules_path))

        registered_modules \
            = set(map(lambda m: m.name, ServerModuleManager.all(session)))

        for module_name in detected_modules - registered_modules:
            try:
                ServerModuleManager.load_from_dir(session, module_name)
            except FileNotFoundError as e:
                logging.warning("module path does not contain valid module "
                                f"'{module_name}': {e}")

        for module_name in registered_modules - detected_modules:
            ServerModuleManager.delete(session, module_name)

        for m in ServerModuleManager.all(session):
            ServerModuleManager(session, m.name).update_versions()
