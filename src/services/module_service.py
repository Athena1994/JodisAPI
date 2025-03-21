

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
