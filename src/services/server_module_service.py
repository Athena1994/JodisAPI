

import glob
import logging
import os
from model.local_model.server_modules.component_provider \
      import ComponentProvider
from model.local_model.server_modules.module_control import ModuleControl
from utils.model_managing.subject_manager import SubjectManager


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

    def get_server_version(self):
        return self._version

    def refresh_modules(self, base_path: str):
        module_files = _find_all_modules(base_path)
        modules = []
        for module_file in module_files:
            try:
                modules.append(ModuleControl(module_file))
            except Exception as e:
                logging.warning(f"Failed to load module from {module_file}: "
                                f"{e}")
