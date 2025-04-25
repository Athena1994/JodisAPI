from dataclasses import dataclass
import json
import logging
from pathlib import Path

from aithena.utils.config_utils import assert_fields_in_dict

from model.local_model.server_modules.utils.component_provider\
    import ComponentProvider
from model.local_model.server_modules.utils.error import Error
from model.local_model.server_modules.utils.module_fs_control \
    import ModuleFSControl
import hashlib

from model.local_model.server_modules.sub_modules.sub_module_control\
    import SubModuleControl
from model.local_model.server_modules.utils.state import State


class ModuleControl:

    def __init__(self, module_path: str):

        self._sub_modules = list()
        self._cfg = None
        self._error = None
        self._fs = None
        self._cp = None

        self._state = State.NOT_INITIALIZED

        self._log = logging.getLogger(__name__)

        self._initialize(module_path)

    def _initialize(self, module_path: str):

        # load module.json
        if not Path(module_path).exists():
            raise FileNotFoundError(f"Config file '{module_path}' not found!")
        module_json = json.load(open(module_path))

        # assert config is valid
        try:
            self._cfg = ModuleControl.Config.from_json(module_json)
        except Exception as e:
            self._error = Error(
                description=f"Configuration file '{module_json}' invalid! {e}",
                code=Error.Type.CFG_INVALID)
            return

        self._log = logging.getLogger(f"{self}")

        # initialize file system control
        self._fs = ModuleFSControl(Path(module_path).parent,
                                   self._cfg.path_cfg)
        if not self._fs.is_valid():
            self._error = Error(
                description="File structure invalid!",
                code=Error.Type.FILE_STRUCTURE_INVALID)
            return

        self._cp = ComponentProvider(self._fs.get_src_path())

        # load sub-modules
        for i, sub_module_cfg in enumerate(self._cfg.sub_module_cfgs):
            try:
                self._load_sub_module(sub_module_cfg, i)
            except Exception as e:
                self._log.warning(f"Failed to load sub-module #{i}: {e}")

        self._state = State.INITIALIZED

    def _load_sub_module(self, sub_module_cfg: dict, ix: int):
        """
        Loads a sub-module from the configuration.
        """
        sub_module = SubModuleControl(
            json=sub_module_cfg,
            id=ix,
            parent_name=f"{self}",
            cp=self._cp, fs=self._fs)
        self._sub_modules.append(sub_module)
        self._log.info(f"Loaded sub-module: {sub_module}")

    def __str__(self):
        if self._cfg is None:
            return "(ModuleControl: InvalidConfig)"
        return f"(ModuleControl: {self._cfg.name}:{self._cfg.module_version})"

    # --- properties ---------------------------------

    @property
    def error(self):
        return self._error

    @property
    def fs(self):
        if self._fs is None:
            raise ValueError("File system control is not initialized.")
        return self._fs

    @property
    def state(self):
        if self._error is not None:
            return State.ERROR
        return self._state

    # --- getter --------------------------------------

    def get_identifier(self) -> str:
        if self._cfg is None:
            raise ValueError("ModuleControl is not initialized properly.")
        identifier = f"{self._cfg.name}:{self._cfg.module_version}"
        return hashlib.sha256(identifier.encode()).hexdigest()

    def has_valid_config(self):
        return self._cfg is not None

    def has_error(self):
        return self._error is not None

    # --- data classes --------------------------------

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
