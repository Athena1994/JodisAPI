import json
import logging
import os
import re
from model.exeptions import StateError
from model.local_model import models
from model.local_model.server_module_version_manager \
    import ServerModuleVersionManager
from utils import path_builder
from utils.model_managing.subject_session import SubjectSession
import app_constants


class ServerModuleManager:

    MODULE_CONFIG_FILE_NAME = "config.json"

    # --- creation/destruction -------------------

    def __init__(self, session: SubjectSession, module_name: str):
        self._session = session
        self._model: models.ServerModule \
            = session.get(models.ServerModule, module_name, True)

    """
    Tries to load complete server module from module path with given name.
    """
    @staticmethod
    def create(session: SubjectSession, name: str)\
            -> models.ServerModule:
        module = models.ServerModule(name=name, version_ids=dict())
        session.add(module)
        return module

    @staticmethod
    def delete(session: SubjectSession, module_name: str) -> None:
        logging.info(f"Deleting server module '{module_name}'")
        module = ServerModuleManager(session, module_name)

        if module.is_running():
            raise StateError()

        session.delete(module.model())

    @staticmethod
    def exists(session: SubjectSession, module_name: str) -> bool:
        return session.exists(models.ServerModule, module_name)

    @staticmethod
    def all(session: SubjectSession) -> set[models.ServerModule]:
        return session.get_all(models.ServerModule)

    # --- control ----------------------------

    """
    Updates the versions of the module by detecting all versions in the module.
    Abandoned versions are removed, new versions are added and changed versions
    are updated.

    Note: Module needs to be stopped before updating versions.
    """
    def load_versions(self) -> None:
        if self.is_running():
            raise StateError("Cannot update versions while module is running")

        module = self.model()
        path = path_builder.build_path(module.name, app_constants.MODULE_DOMAIN)

        # detect version directories
        version_filter = re.compile(r"\d+\.\d+\.\d+")
        detected_versions = set(filter(lambda m: version_filter.fullmatch(m),
                                       os.listdir(path)))
        registered_versions = set(module.version_ids.keys())

        # add new versions
        for new_version in detected_versions - registered_versions:
            try:
                version = ServerModuleVersionManager.load_from_dir(
                    self._session, path, new_version)
                module.version_ids[new_version] = version.id
            except FileNotFoundError as e:
                logging.warning(f"Module '{module.name}' version "
                                f"'{new_version}' not valid: {e}")

        # remove abandoned versions
        if module.active_version not in detected_versions:
            module.active_version = None

        for abandoned_version in registered_versions - detected_versions:
            ServerModuleVersionManager(
                self._session, module.version_ids[abandoned_version]).delete()
            del module.version_ids[abandoned_version]

        # update versions
        for version in (ServerModuleVersionManager.get_versions_by_ids(
                self._session, module.version_ids.values())):
            ServerModuleVersionManager(self._session,
                                       version.id).validate_file_structure()

    def reload(self) -> None:
        module = self.model()
        logging.info(f"Loading server module '{module.name}'")

        if self.is_running():
            raise StateError("Cannot reload module while it is running")

        # clean up old version
        for version in ServerModuleVersionManager.get_versions_by_ids(
                self._session, module.version_ids.values()):
            ServerModuleVersionManager(self._session,
                                       version.id).delete()
        module.version_ids.clear()
        module.active_version = None
        module.error = None

        module_path = path_builder.build_path(module.name,
                                              app_constants.MODULE_DOMAIN)

        # load cfg file
        cfg_file = os.path.join(module_path,
                                ServerModuleManager.MODULE_CONFIG_FILE_NAME)
        if not os.path.exists(cfg_file):
            module.error = models.ModuleError(
                code=models.ModuleError.Type.CFG_MISSING,
                description=f"config file '{cfg_file}' not found",
                name="ConfigFileMissing")
            raise FileNotFoundError(f"Configuration file '{cfg_file}' not "
                                    "found!")

        cfg: dict = {}

        try:
            with open(cfg_file, 'r') as f:
                cfg = json.load(f)

            if 'description' in cfg:
                module.description = cfg['description']

            if 'enabled' in cfg:
                module.enabled = cfg['enabled']

            if 'autostart' in cfg:
                module.autostart = cfg['autostart']

        except json.JSONDecodeError as e:
            module.error = models.ModuleError(
                code=models.ModuleError.Type.CFG_INVALID,
                description=f"config file has invalid format: {e}",
                name="ConfigParseError")
            logging.warning(f"Error loading module '{module.name}': {e}")

        ServerModuleManager(self._session, module.name).load_versions()

    # --- getter ------------------------------

    def model(self) -> models.ServerModule:
        return self._model

    def get_active_version(self) -> models.ServerModuleVersion | None:
        model = self.model()
        if model.active_version is None:
            return None

        if model.active_version not in model.version_ids:
            return None

        return ServerModuleVersionManager(
            self._session, model.version_ids[model.active_version]).model()

    def get_version(self, version: str) -> models.ServerModuleVersion:
        model = self.model()
        if version not in model.version_ids:
            raise KeyError(f"Version '{version}' not found")
        return ServerModuleVersionManager(
            self._session, model.version_ids[version]).model()

    def is_running(self) -> bool:
        active_version = self.get_active_version()
        return active_version.running if active_version else False

    def has_error(self) -> bool:
        return self.model().error is not None

    def get_last_error(self) -> models.ModuleError | None:
        return self.model().error
