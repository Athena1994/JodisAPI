

from abc import abstractmethod

from services.server_modules.utils.js_component_provider \
    import JSComponentProvider
from services.server_modules.utils.module_identifier import ModuleIdentifier
from services.server_modules.utils.py_module_provider import PyModuleProvider
from services.server_modules.utils.web_component import WebComponent

from jodisutils.config.decorator import config
from jodisutils.config.attribute import Attribute


class SubModule:

    def __init__(self, module_id: ModuleIdentifier, sub_id: int,
                 type: str,
                 cp: JSComponentProvider, mp: PyModuleProvider):
        self._type = type
        self._sub_id = sub_id
        self._module_id = module_id.id
        self._cp = cp
        self._mp = mp

    # --- methods ----------------------------------------

    @abstractmethod
    def start(self) -> None:
        pass

    @abstractmethod
    def stop(self) -> None:
        pass

    @abstractmethod
    def is_busy(self) -> bool:
        pass

    def get_component(self, component: str) -> WebComponent:
        return self._cp.get_component(self._sub_id, component)

    # --- property ---------------------------------------

    @property
    def module_id(self) -> int:
        return self._module_id

    @property
    def sub_id(self) -> int:
        return self._sub_id

    @property
    def cp(self) -> JSComponentProvider:
        return self._cp

    @property
    def mp(self) -> PyModuleProvider:
        return self._mp

    def __str__(self):
        return f"SubModule#{self._sub_id} ({self._type})"

    @config
    class Config:
        type: str = Attribute(required=True)
        options: dict = Attribute(default={})

        # @staticmethod
        # def schema() -> dict:
        #     return {
        #         "type": "object",
        #         "properties": {
        #             "type": {
        #                 "type": "string",
        #                 "description": "Type of the sub-module."
        #             },
        #             "options": {
        #                 "type": "object",
        #                 "description": "Options for the sub-module.",
        #                 "default": {}
        #             },
        #         },
        #         "required": ["type"]
        #     }
