
from dataclasses import dataclass
import logging
from logging import Logger

from model.local_model.server_modules.sub_modules.sub_module_factory\
      import SubModuleFactory
from model.local_model.server_modules.utils.component_provider \
      import ComponentProvider
from model.local_model.server_modules.utils.module_fs_control \
    import ModuleFSControl

from model.local_model.server_modules.utils.error import Error
from model.local_model.server_modules.utils.state import State


class SubModuleControl:

    def __init__(self, json: dict,
                 parent_name: str, id: int,
                 cp: ComponentProvider, fs: ModuleFSControl):

        try:
            cfg = SubModuleControl.Config.from_json(json)
        except KeyError as e:
            self.error = Error(
                description=f"Failed to load sub-module config: {e}",
                code=Error.Type.CFG_INVALID)
            return

        self._id = id
        self._cp = cp
        self._fs = fs
        self._log = logging.getLogger(f"{parent_name}.SubModule#{id}")

        self._state = State.NOT_INITIALIZED
        self._error: Error = None
        self._sub_module = None

        cp.register_sub_module(id, cfg.js_module)

        try:
            self._sub_module = SubModuleFactory(id, cp).create(
                cfg.type, cfg.options)
            self._state = State.INITIALIZED
        except Exception as e:
            self.error = Error(
                description=f"Failed to create sub-module: {e}",
                code=Error.Type.INITIALIZATION_FAILED)
            return

    @property
    def state(self) -> str:
        if self._error is not None:
            return State.ERROR
        return self._state

    @property
    def error(self) -> Error:
        return self._error

    @error.setter
    def error(self, error: Error):
        self._error = error
        if error is not None:
            logging.warning(error)

    @property
    def cp(self) -> ComponentProvider:
        return self._cp

    @property
    def fs(self) -> ModuleFSControl:
        return self._fs

    @property
    def log(self) -> Logger:
        return self._log

    def __str__(self):
        if self._error is None:
            return f"({self._sub_module})"
        return f"(SubModule #{self._id}, error)"

    @dataclass
    class Config:
        js_module: str
        type: str
        options: dict

        @staticmethod
        def from_json(cfg: dict):
            if 'js-module' not in cfg:
                raise KeyError("Key 'js-module' not found in configuration.")
            if 'type' not in cfg:
                raise KeyError("Key 'type' not found in configuration.")
            return SubModuleControl.Config(
                js_module=cfg['js-module'],
                type=cfg['type'],
                options=cfg.get('options', {})
            )
