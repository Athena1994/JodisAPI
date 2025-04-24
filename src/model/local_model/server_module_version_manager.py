
import json
import logging
import os
from model.exeptions import StateError
from model.local_model import models
from model.local_model.module_interface.component_provider import ComponentProvider
from utils import hash_utils
from utils.model_managing.subject_session import SubjectSession
from _hashlib import HASH as Hash

from aithena.utils.config_utils import assert_fields_in_dict


class ServerModuleVersionManager:

    CONFIG_FILE_NAME = "config.json"

    # --- creation/destruction -------------------

    def __init__(self, session: SubjectSession, id: int):
        self._session = session
        self._model: models.ServerModuleVersion \
            = session.get(models.ServerModuleVersion, id, True)

    @staticmethod
    def get_versions_by_ids(session: SubjectSession, ids: list[int])\
            -> list[models.ServerModuleVersion]:
        return [session.get(models.ServerModuleVersion, id, True) for id in ids]

    """
        Loads module version from directory without initialization and adds
        instance to session.

        Note: If the version is not found, a FileNotFoundError is raised.
    """
    @staticmethod
    def load_from_dir(session: SubjectSession,
                      module_path: str, version_str: str) \
            -> models.ServerModuleVersion:

        version_path = os.path.join(module_path, version_str)

        cfg_file = os.path.join(
            version_path, ServerModuleVersionManager.CONFIG_FILE_NAME)

        version = models.ServerModuleVersion(
                version=version_str,
                base_path=version_path)

        if not os.path.exists(module_path):
            raise FileNotFoundError(f"Module path '{module_path}' not found!")

        if not os.path.exists(version_path):
            raise FileNotFoundError(f"Version path '{version_path}' not found!")

        try:
            if not os.path.exists(cfg_file):
                raise models.ModuleError(
                    name='ConfigPathError',
                    description=f"Configuration file '{cfg_file}' not found!",
                    code=models.ModuleError.Type.PATH_NOT_FOUND)

            cfg: dict = {}

            try:
                with open(cfg_file, 'r') as f:
                    cfg = json.load(f)
                assert_fields_in_dict(cfg, ['apiVersion', 'moduleVersion'])
            except json.JSONDecodeError:
                raise models.ModuleError(
                    name='ConfigParseError',
                    description=f"Configuration file '{cfg_file}' not valid "
                                "JSON!",
                    code=models.ModuleError.Type.CFG_INVALID)
            except ValueError as e:
                raise models.ModuleError(
                    name='MissingConfigKeyError',
                    description=f"Configuration file '{cfg_file}' invalid! {e}",
                    code=models.ModuleError.Type.CFG_INVALID)

            if not cfg['moduleVersion'] == version_str:
                raise models.ModuleError(
                    name='ConfigVersionMismatch',
                    description=f"Version '{version_str}' does not match "
                                "configuration version "
                                f"'{cfg['moduleVersion']}'",
                    code=models.ModuleError.Type.CFG_INVALID)

            version.api_version = cfg['apiVersion']

            version.src_dir = cfg.get('src_dir', 'src')
            version.working_dir = cfg.get('working_dir', 'rt')

            # TODO: ensure src hash matches security hash

        except models.ModuleError as e:
            logger = logging.getLogger()
            logger.warning(f"Invalid Version: {e}")
            version.error = e

        session.add(version)
        return version

    def delete(self) -> None:
        self._session.delete(self.model())

# --- private methods -------------------
    def _validate_src(self):
        model = self.model()
        new_hash = self.get_src_hash_str()

        valid = False

        try:
            valid = os.path.exists(self.get_src_path())

        finally:
            model.last_validation_succeeded = valid
            model.last_src_hash = new_hash

# --- instance control -------------------

    """
        Initializes version directory and validates src.
    """
    def validate_file_structure(self) -> bool:
        model = self.model()

        if model.initialized and self.is_src_validated():
            return True

        if not os.path.exists(self.get_working_path()):
            os.makedirs(self.get_working_path())

        self._validate_src()

        model.initialized = True

        # TODO: auto start version -> add job queue

        return True

    def start(self) -> bool:
        model = self.model()

        if not model.initialized:
            raise StateError("Failed to start. Version not initialized!")

        if model.running:
            return True

        if not self.is_src_validated():
            raise StateError("Failed to start. Source not validated!")

        # TODO start code
        model.running = True

        return model.running

    def stop(self) -> bool:
        model = self.model()

        if not model.running:
            return True

        # TODO stop code
        model.running = False

        return model.running

# --- getter -------------------
    def get_src_path(self):
        model = self.model()
        return os.path.join(model.base_path, model.src_dir)

    def get_working_path(self):
        model = self.model()
        return os.path.join(model.base_path, model.working_dir)

    def get_src_hash(self) -> Hash:
        return hash_utils.hash_dir(self.get_src_path())

    def get_src_hash_str(self) -> str:
        return str(self.get_src_hash().hexdigest())

    def get_config_hash(self) -> Hash:
        return hash_utils.hash_file(
            os.path.join(self.model().base_path,
                         ServerModuleVersionManager.CONFIG_FILE_NAME))

    def has_error(self) -> bool:
        return self.model().error is not None

    def is_running(self):
        return self.model().running

    def is_initialized(self):
        return self.model().initialized

    def is_src_validated(self):
        if self.get_src_hash_str() == self.model().last_src_hash:
            return self.model().last_validation_succeeded
        return False

    def model(self) -> models.ServerModuleVersion:
        return self._model
