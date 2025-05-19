import json
import logging
from pathlib import Path
import traceback
from typing import List

from injector import Injector, singleton

from services.server_modules.sub_modules.sub_module_factory \
    import SubModuleFactory
from services.server_modules.utils.js_component_provider \
    import JSComponentProvider
from services.server_modules.utils.error import Error
from services.server_modules.utils.module_fs_control \
    import ModuleFSControl
from services.server_modules.sub_modules.sub_module_control\
    import SubModuleControl
from services.server_modules.utils.module_identifier import ModuleIdentifier
from services.server_modules.utils.py_module_provider import PyModuleProvider
from services.server_modules.utils.state import State

from utils.config.decorator import config
from utils.config.attribute import Attribute


class ModuleControl:

    def __init__(self, module_path: Path, injector: Injector):

        self._sub_modules: List[SubModuleControl] = list()
        self._identifier: ModuleIdentifier = None

        self._error = None

        self._fs = None
        self._cp = None
        self._mp = None

        self._sub_module_factory = None

        self._state = State.NOT_INITIALIZED

        logging.info(f"Initializing module control for '{module_path}'")

        # load module.json
        if not module_path.exists():
            raise FileNotFoundError(f"Config file '{module_path}' not found!")
        module_json = json.load(open(module_path))

        # assert config is valid
        try:
            cfg = ModuleControl.Config(**module_json)
        except Exception as e:
            self.error = Error(
                description=f"Configuration file '{module_json}' invalid! {e}",
                code=Error.Type.CFG_INVALID,
                traceback=traceback.format_exc())
            return

        self._identifier = ModuleIdentifier(cfg.name, cfg.module_version)

        # initialize file system control
        logging.debug(f"Initializing file system control: {module_path}")
        self._fs = ModuleFSControl(module_path.parent,
                                   cfg.path_cfg)
        if not self._fs.is_valid:
            self.error = Error(
                description="File structure invalid!",
                code=Error.Type.FILE_STRUCTURE_INVALID,
                traceback=traceback.format_exc())
            return

        try:
            self._cp = JSComponentProvider(
                self._identifier,
                Path(cfg.name).joinpath(cfg.module_version))
            self._mp = PyModuleProvider(self._fs.get_src_path())
        except Exception as e:
            self.error = Error(
                description=f"Failed to create provider: {e}",
                code=Error.Type.INITIALIZATION_FAILED,
                traceback=traceback.format_exc())
            return

        # load sub-modules
        self._injector = injector.create_child_injector()
        self._injector.binder.bind(ModuleFSControl,
                                   to=self._fs, scope=singleton)
        self._injector.binder.bind(PyModuleProvider,
                                   to=self._mp, scope=singleton)
        self._injector.binder.bind(JSComponentProvider,
                                   to=self._cp, scope=singleton)

        self._sub_module_factory = SubModuleFactory(
            self.id, self._cp, self._injector)

        for i, sub_module_cfg in enumerate(cfg.sub_module_cfgs):
            try:
                logging.debug(f"Loading sub-module #{i}: {sub_module_cfg}")
                sm = SubModuleControl(sub_module_cfg, i,
                                      self._sub_module_factory)
                self._sub_modules.append(sm)
            except Exception as e:
                logging.warning(f"Failed to load sub-module #{i}: {e}")

        logging.info(f"Module {self.id} initiialized!")

        self._state = State.INITIALIZED

    def __str__(self):
        if not self.initialized:
            return "(ModuleControl: InvalidConfig)"
        return f"(ModuleControl: {self.id})"

    # --- methods ------------------------------------

    def start(self):
        if self._state != State.INITIALIZED:
            raise ValueError(f"Invalid State {self._state}: "
                             f"expected {State.INITIALIZED}")
        try:
            for m in filter(lambda m: m.state == State.INITIALIZED,
                            self._sub_modules):
                self._injector.call_with_injection(m.start)
            self._state = State.READY
        except Exception:
            self.error = Error(
                "Failed to start sub modules.",
                Error.Type.INTERNAL_ERROR,
                traceback=traceback.format_exc()
            )

    def stop(self):
        if self._state == State.INITIALIZED:
            raise ValueError(f"Invalid State {self._state}")
        try:
            for m in self._sub_modules:
                self._injector.call_with_injection(m.stop)
                self._state = State.INITIALIZED
        except Exception:
            self.error = Error(
                "Failed to stop sub module.",
                Error.Type.INTERNAL_ERROR,
                traceback=traceback.format_exc()
            )

    # --- properties ---------------------------------

    @property
    def error(self):
        return self._error

    @error.setter
    def error(self, value):
        self._error = value
        logging.warning(f"ModuleControl error: {value}")

    @property
    def fs(self):
        if self._fs is None:
            raise ValueError("File system control is not initialized.")
        return self._fs

    @property
    def state(self):
        if self._error is not None:
            return State.ERROR

        if (self._state == State.READY and
           any([m.state == State.BUSY for m in self._sub_modules])):
            return State.BUSY

        return self._state

    @property
    def id(self):
        if not self._identifier:
            raise ValueError("ModuleControl is not initialized.")
        return self._identifier

    @property
    def initialized(self) -> bool:
        return self._state != State.NOT_INITIALIZED

    def has_error(self):
        return self._error is not None

    # --- data classes --------------------------------

    @config
    class Config:
        name: str = Attribute(required=True)
        path_cfg: ModuleFSControl.Config = Attribute('paths')
        module_version: str = Attribute(
            'versions', json_type=dict, deserializer=lambda x: x['module'],
            required=True)
        sub_module_cfgs: list = Attribute('sub-modules')

        # @staticmethod
        # def schema() -> dict:
        #     return {
        #         "type": "object",
        #         "properties": {
        #             "name": {"type": "string"},
        #             "paths": ModuleFSControl.Config.schema(),
        #             "versions": {
        #                 "type": "object",
        #                 "properties": {
        #                     "module": {"type": "string"},
        #                     "api": {"type": "string"},
        #                 },
        #                 "required": ["module", "api"]
        #             },
        #             "sub-modules": {
        #                 "type": "array",

        #             }
        #         },
        #     }
