
import logging
import os
from pathlib import Path
import traceback

from injector import Injector
import app_constants
from model.local_model import models
from model.local_model.server_module_manager import ServerModuleManager
from services.server_modules.module_control import ModuleControl
from services.server_modules.utils.state import State
from jodisutils.files import path_builder
from jodisutils.model_managing.subject_manager import SubjectManager


def _find_all_modules(base_path: str):
    module_files = []

    # find all module.json files under base_path/*/
    root, module_dirs, _ = next(os.walk(base_path))

    for module_dir in module_dirs:
        module_root, version_dirs, _ = next(os.walk(Path(root, module_dir)))
        for dir in version_dirs:
            file = Path(module_root, dir, "module.json")
            if file.exists():
                module_files.append(file)

    logging.info(f"Found {len(module_files)} modules in {base_path}")

    return module_files


class ServerModuleService:

    def __init__(self, sm: SubjectManager):
        self._sm = sm
        self._version = '0.0.1'

        self._injector = None

    def set_injector(self, injector: Injector):
        self._injector = injector

    def get_server_version(self):
        return self._version

    def start_all(self):
        logging.info('starting all initialized modules...')
        with self._sm.create_session() as session:
            modules = ServerModuleManager.all(session)

            for m in modules:
                if m.control.state == State.INITIALIZED:
                    logging.info(f'starting {m}')
                    m.control.start()

    def refresh_modules(self):
        logging.info("Refreshing modules...")

        if self._injector is None:
            raise ValueError("Injector not set!")

        base_path = path_builder.build_path("", app_constants.MODULE_DOMAIN)

        module_files = _find_all_modules(base_path)

        found_module_ids = dict()

        with self._sm.create_session() as session:
            for module_file in module_files:
                # load module control
                try:
                    mc = ModuleControl(module_file, self._injector)
                except Exception as e:
                    logging.warning(f"Failed to load module from {module_file}:"
                                    f" {e}\n{traceback.format_exc()}")
                    continue

                if not mc.initialized:
                    logging.warning(f"Failed to load {module_file}! "
                                    f"{mc.error}")
                    continue

                # check if module with same id already exists
                if mc.id in found_module_ids:
                    logging.warning(
                        f"Duplicate module id {mc.id} found in "
                        f"{module_file} and {found_module_ids[mc.id]}"
                        f" - skipping {module_file}")
                    continue
                found_module_ids[mc.id] = module_file

                # add new modules to the database
                if not ServerModuleManager.exists(session, mc.id):
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
