

import os
import app_constants
from model.local_model.server_module_manager import ServerModuleManager
from utils import path_builder
from utils.model_managing.subject_session import SubjectSession


class ModuleService:

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

        modules_path = path_builder.build_path('', app_constants.MODULE_DOMAIN)

        # create module path if it does not exist
        if not os.path.exists(modules_path):
            os.makedirs(modules_path)

        # find all modules in module path
        detected_modules = set(os.listdir(modules_path))

        registered_modules \
            = map(lambda m: m.name, ServerModuleManager.all(session))

        for module_name in detected_modules - registered_modules:
            ServerModuleManager.load(session, module_name)

        for module_name in registered_modules - detected_modules:
            ServerModuleManager.delete(session, module_name)

        for m in ServerModuleManager.all(session):
            ServerModuleManager(session, m.name).update_versions(session)

        session.commit()
