

import glob
import logging
import os
from typing import List, Tuple
import app_constants
from model.exeptions import StateError
from model.local_model.models import ServerModule, ServerModuleVersion
from model.local_model.module_interface.module_control import ModuleControl
from model.local_model.module_interface.component_provider \
    import ComponentProvider
from model.local_model.server_module_manager import ServerModuleManager
from model.local_model.server_module_version_manager \
    import ServerModuleVersionManager
from utils import path_builder
from utils.model_managing.subject_manager import SubjectManager
from utils.model_managing.subject_session import SubjectSession


def _find_all_modules(base_path: str):
    module_files = []
    for root, _, _ in os.walk(base_path):
        module_files.extend(glob.glob(os.path.join(root, "module.json")))
    return module_files


class ServerModuleService:

    def __init__(self, sm: SubjectManager, cp: ComponentProvider):
        self._sm = sm
        self._cp = cp
        self._version = '0.0.1'

    def get_version(self):
        return self._version

    def get_module_version(self, module_name: str, version: str) \
            -> ServerModuleVersion:
        with self._sm.create_session() as session:
            return ServerModuleManager(session, module_name)\
                .get_version(version)

    def get_module(self, module_name: str) \
            -> Tuple[ServerModule, List[ServerModuleVersion],
                     ServerModuleVersion]:
        with self._sm.create_session() as session:
            module = ServerModuleManager(session, module_name)
            versions = ServerModuleVersionManager.get_versions_by_ids(
                session, module.model().version_ids.values())
            active_version = module.get_active_version()
            return module.model(), versions, active_version

    def get_modules(self) -> List[Tuple[ServerModule, ServerModuleVersion]]:
        with self._sm.create_session() as session:
            return [(m,
                     ServerModuleManager(session, m.name).get_active_version())
                    for m in ServerModuleManager.all(session)]

    def refresh_modules(self, base_path: str):
        module_files = _find_all_modules(base_path)
        modules = []
        for module_file in module_files:
            try:
                modules.append(ModuleControl(module_file))
            except Exception as e:
                logging.warning(f"Failed to load module from {module_file}: "
                                f"{e}")






    # """Detect all modules in the module path and register them. Creates the
    # module path if it does not exist."""
    # @staticmethod
    # def examine_modules(session: SubjectSession) -> None:

    #     # assert all modules have stopped
    #     for m in ServerModuleManager.all(session):
    #         if ServerModuleManager(session, m.name).is_running():
    #             raise StateError(f"Module '{m.name}' is still running!")

    #     modules_path = path_builder.build_path('', app_constants.MODULE_DOMAIN)

    #     # create module path if it does not exist
    #     if not os.path.exists(modules_path):
    #         os.makedirs(modules_path)

    #     # find all modules in module path
    #     detected_modules = set(os.listdir(modules_path))

    #     registered_modules \
    #         = set(map(lambda m: m.name, ServerModuleManager.all(session)))

    #     for module_name in detected_modules - registered_modules:
    #         try:
    #             ServerModuleManager.create(session, module_name)
    #             ServerModuleManager(session, module_name).reload()
    #         except FileNotFoundError as e:
    #             logging.warning("module path does not contain valid module "
    #                             f"'{module_name}': {e}")

    #     for module_name in registered_modules - detected_modules:
    #         ServerModuleManager.delete(session, module_name)

    #     for m in ServerModuleManager.all(session):
    #         ServerModuleManager(session, m.name).load_versions()

    # def reload_module(self, module_name: str) -> ServerModule:
    #     """Reloads the module and returns the module object."""
    #     with self._sm.create_session() as session:
    #         module = ServerModuleManager(session, module_name)
    #         try:
    #             module.reload()
    #         except Exception:
    #             pass

    #         session.commit()

    #         logging.info(module.model().version_ids)
    #         return module.model()

    # def initialize(self, sm: SubjectManager):
    #     with sm.create_session() as session:
    #         self.examine_modules(session)
    #         session.commit()
