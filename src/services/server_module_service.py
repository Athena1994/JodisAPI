

import glob
import logging
import os
import app_constants
from model.local_model import models
from model.local_model.server_module_manager import ServerModuleManager
from model.local_model.server_modules.module_control import ModuleControl
from utils import path_builder
from utils.model_managing.subject_manager import SubjectManager


def _find_all_modules(base_path: str):
    module_files = []
    for root, _, _ in os.walk(base_path):
        module_files.extend(glob.glob(os.path.join(root, "module.json")))
    return module_files


class ServerModuleService:

    def __init__(self, sm: SubjectManager):
        self._sm = sm
        self._version = '0.0.1'

        self.refresh_modules()

    def get_server_version(self):
        return self._version

    def refresh_modules(self):
        logging.info("Refreshing modules...")
        base_path = path_builder.build_path("", app_constants.MODULE_DOMAIN)

        module_files = _find_all_modules(base_path)

        found_module_ids = dict()

        with self._sm.create_session() as session:
            for module_file in module_files:
                # load module control
                try:
                    mc = ModuleControl(module_file)
                except Exception as e:
                    logging.warning(f"Failed to load module from {module_file}:"
                                    f" {e}")
                    continue

                if not mc.has_valid_config():
                    logging.warning(f"Failed to load {module_file}! "
                                    f"{mc.get_error()}")
                    continue

                module_id = mc.get_identifier()

                # check if module with same id already exists
                if module_id in found_module_ids:
                    logging.warning(
                        f"Duplicate module id {module_id} found in "
                        f"{module_file} and {found_module_ids[module_id]}"
                        f" - skipping {module_file}")
                    continue
                found_module_ids[module_id] = module_file

                # add new modules to the database
                if not ServerModuleManager.exists(session, module_id):
                    sm: models.ServerModule \
                        = ServerModuleManager.create(session, mc)
                    logging.info(f"Registered {sm}")
                    continue

            # remove modules that are not in the file system anymore
            missing_ids = ServerModuleManager.get_all_ids(session).difference(
                found_module_ids.keys())
            for id in missing_ids:
                ServerModuleManager.delete(session, id)
                logging.info(f"Unregistered {id}")

            # TODO: update dirty modules

            session.commit()
