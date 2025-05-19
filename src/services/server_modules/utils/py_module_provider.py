
from pathlib import Path
from types import ModuleType
from typing import Dict, Tuple

from services.server_modules.utils.py_component import PyComponent

import importlib.util as importlib_util


class PyModuleProvider:
    def __init__(self, src_path: str):
        self._src_path = Path(src_path)
        if not self._src_path.exists():
            raise ValueError(f"Base path {self._src_path} does not exist.")

        self._modules: Dict[str, ModuleType] = dict()
        self._classes: Dict[str, Tuple[str, str]] = dict()
        self._exports: Dict[str, PyComponent] = dict()

    def validate_component(self, component: PyComponent):
        if component.file is None:
            raise ValueError("Component file path is None.")
        if not component.file.exists():
            raise ValueError(f"Component file path {component.file} "
                             "does not exist.")

    def register_module(self, file: str, module_key: str):
        if module_key in self._modules:
            raise ValueError(f"Module {module_key} already registered.")

        module_path = Path.joinpath(self._src_path, file)
        if not module_path.exists():
            raise ValueError(f"Module path {module_path} does not exist.")

        spec = importlib_util.spec_from_file_location(module_key, module_path)
        module = importlib_util.module_from_spec(spec)
        spec.loader.exec_module(module)

        self._modules[module_key] = module

    def register_export(self, file: str, class_name: str, key: str):
        if key in self._exports:
            raise ValueError(f"Export {key} already registered.")

        f = self._src_path.joinpath(file)
        if not f.exists():
            raise ValueError(f"Export file path {f} does not exist.")

        self._exports[key] = PyComponent(f, class_name)

    def register_class(self, module_key: str, class_name: str, key: str):

        if module_key not in self._modules:
            raise ValueError(f"Module {module_key} not registered.")
        if key in self._classes:
            raise ValueError(f"Class {key} already registered.")

        self._classes[key] = (module_key, class_name)

    def create_class(self, key: str, *args):
        if key not in self._classes:
            raise ValueError(f"Class {key} not registered.")

        module_name, class_name = self._classes[key]
        if module_name not in self._modules:
            raise ValueError(f"Module {module_name} not registered.")

        module = self._modules[module_name]
        cls = getattr(module, class_name)
        return cls(*args)

    def get_export(self, key: str):
        if key not in self._exports:
            raise ValueError(f"Export {key} not registered.")
        return self._exports[key]
