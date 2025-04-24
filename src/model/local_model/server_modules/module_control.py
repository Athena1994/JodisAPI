from dataclasses import dataclass
import enum
import json
from pathlib import Path

from utils.config_utils import assert_fields_in_dict

from model.local_model.server_modules.module_fs_control import ModuleFSControl


class ModuleControl:

    @dataclass
    class Config:
        name: str
        path_cfg: ModuleFSControl.Config
        module_version: str
        sub_module_cfgs: list

        @staticmethod
        def from_json(cfg: dict):
            assert_fields_in_dict(
                cfg,
                ['name', 'paths', 'versions', 'sub-modules'])
            assert_fields_in_dict(
                cfg['versions'],
                ['module'])
            return ModuleControl.Config(
                name=cfg["name"],
                path_cfg=ModuleFSControl.Config.from_json(cfg['paths']),
                module_version=cfg['versions']['module'],
                sub_module_cfgs=cfg['sub-modules'])

    @dataclass
    class Error:
        class Type(enum.Enum):
            PATH_NOT_FOUND = "path_not_found"
            CFG_INVALID = "config_invalid"
            UNKNOWN = "unkown",
            FILE_STRUCTURE_INVALID = "file_structure_invalid"

        description: str
        code: Type

        def __str__(self):
            return f"{self.name}({self.code}): {self.description}"

    def _get_cfg(self, key: str):
        """
        Returns the value of the given key in the configuration.
        """
        if key not in self._cfg:
            raise KeyError(f"Key '{key}' not found in configuration.")
        return self._cfg[key]

    def __init__(self, module_path: str):

        self._sub_modules = list()
        self._cfg = None
        self._error = None

        if not Path(module_path).exists():
            raise FileNotFoundError(f"Config file '{module_path}' not found!")

        module_json = json.load(open(module_path))

        try:
            self._cfg = ModuleControl.Config.from_json(module_json)
        except Exception as e:
            self._error = ModuleControl.Error(
                description=f"Configuration file '{module_json}' invalid! {e}",
                code=ModuleControl.Error.Type.CFG_INVALID)
            return

        self._fs = ModuleFSControl(Path(module_path).parent,
                                   self._cfg.path_cfg)

        if not self._fs.is_valid():
            self._error = ModuleControl.Error(
                description="File structure invalid!",
                code=ModuleControl.Error.Type.FILE_STRUCTURE_INVALID)
            return
