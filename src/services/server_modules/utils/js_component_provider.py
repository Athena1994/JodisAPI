
from pathlib import Path

from services.server_modules.utils.module_identifier import ModuleIdentifier
from services.server_modules.utils.web_component import WebComponent


class JSComponentProvider:
    def __init__(self, module_id: ModuleIdentifier, dist_path: Path):
        self._dist_path = dist_path
        self._base_str = module_id.name+":"+module_id.version+":"

        self._smid_components = dict()

        self._components = dict()

    def register_sub_module(self, sub_module_id) -> None:
        """
        Register js-module file with a sub-module.
        """
        self._smid_components[sub_module_id] = dict()

    def register_component(self,
                           sub_module_id: int, module_name: str,
                           component_name: str, registry_key) -> None:
        """
        Register a component.
        :param sub_module_id: ID of the sub-module
        :param component_name: Name of the ts-component-class
        :param registry_key: registry key for the component
        """
        if sub_module_id not in self._smid_components:
            self._smid_components[sub_module_id] = dict()

        sm = self._smid_components[sub_module_id]

        if registry_key in sm:
            raise ValueError(f"Component {registry_key} already registered.")

        sm[registry_key] = WebComponent(self._base_str + module_name,
                                        component_name)

        # if sub_module_id not in self._js_modules:
        #     raise ValueError(f"Sub-module ID {sub_module_id} not registered.")
        # if registry_key in self._smid_components[sub_module_id]:
        #     raise ValueError(f"Component {registry_key} already registered.")

        # self._smid_components[sub_module_id][registry_key] = component_name

    def get_js_module_url(self, sub_module_id: int) -> str:
        if sub_module_id not in self._js_modules:
            raise ValueError(f"Sub-module ID {sub_module_id} not registered.")
        return self._js_modules[sub_module_id]

    def get_component_class(self, sub_module_id: int, key: str) -> str:
        if sub_module_id not in self._smid_components:
            raise ValueError(f"Sub-module ID {sub_module_id} not registered.")
        if key not in self._smid_components[sub_module_id]:
            raise ValueError(f"Component {key} not registered.")
        return self._smid_components[sub_module_id][key]

    def get_component(self, sub_module_id: int, key: str) \
            -> WebComponent:
        """
        Get the URL and ts-class of a component.
        :param sub_module_id: ID of the sub-module
        :param key: registry key for the component
        :return: [URL, ts-class] of the component
        """
        if sub_module_id not in self._smid_components:
            raise ValueError(f"Sub-module ID {sub_module_id} not registered.")
        if key not in self._smid_components[sub_module_id]:
            raise ValueError(f"Component {key} not registered.")
        return self._smid_components[sub_module_id][key]
