
from dataclasses import dataclass
import json
import logging
import os
import re
from model.exeptions import StateError
from model.local_model import models
from model.local_model.module_version_manager import ServerModuleVersionManager
from utils import path_builder
from utils.model_managing.subject_session import SubjectSession
from app_config import config as app_config
import app_constants


class ServerModuleManager:

    MODULE_CONFIG_FILE_NAME = "config.json"

    @dataclass
    class Config:
        path: str

        @staticmethod
        def from_dict(cfg: dict) -> 'ServerModuleManager.Config':
            return ServerModuleManager.Config(
                cfg.get('path', 'modules/')
            )

    def __init__(self, session: SubjectSession, module_name: str):
        self._session = session
        self._model: models.ServerModule \
            = session.get(models.ServerModule, module_name, True)

    def model(self) -> models.ServerModule:
        return self._model

    """Tries to load complete server module from module path with given name
    name"""
    @staticmethod
    def load(session: SubjectSession, name: str)\
            -> models.ServerModule:
        logging.info(f"Loading server module '{name}'")

        module_path = path_builder.build_path(app_config.modules.path)

        # load cfg file
        cfg_file = os.path.join(module_path,
                                ServerModuleManager.MODULE_CONFIG_FILE_NAME)
        if not os.path.exists(cfg_file):
            raise FileNotFoundError(f"Configuration file '{cfg_file}' not "
                                    "found!")

        cfg: dict = {}
        with open(cfg_file, 'r') as f:
            cfg = json.load(f)

        module = models.ServerModule(
            name=name,
            description=cfg.get('description', 'No description provided'),
            enabled=cfg.get('enabled', True),
            autostart=cfg.get('autostart', False),
        )

        session.add(module)

        ServerModuleManager(session, name).update_versions()

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

    def get_active_version(self) -> ServerModuleVersionManager | None:
        model = self.model()
        if model.active_version is None:
            return None

        if model.active_version not in model.version_ids:
            return None

        return ServerModuleVersionManager(
            self._session, model.version_ids[model.active_version])

    def is_running(self) -> bool:
        active_version = self.get_active_version()
        return active_version.model().running if active_version else False

    """
    Updates the versions of the module by detecting all versions in the module.
    Abandoned versions are removed, new versions are added and changed versions
    are updated.

    Note: Module needs to be stopped before updating versions.
    """
    def update_versions(self) -> None:
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
            version = ServerModuleVersionManager.load_from_dir(
                self._session, path, new_version)
            module.version_ids[new_version] = version.id

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
            ServerModuleVersionManager(self._session, version.id).initialize_and_validate()


