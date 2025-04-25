
from pathlib import Path

from model.local_model.server_modules.utils.web_component import WebComponent


class ComponentProvider:
    def __init__(self, dist_path: Path):
        self._dist_path = dist_path

        if not self._dist_path.exists():
            raise ValueError(f"Base path {self._dist_path} does not exist.")

        self._js_modules = dict()

        self._smid_components = dict()

    def register_sub_module(self, sub_module_id: int, js_module: str) -> None:
        """
        Register js-module file with a sub-module.
        """
        if sub_module_id in self._js_modules:
            raise ValueError(f"Sub-module ID {sub_module_id} already "
                             "registered.")
        self._js_modules[sub_module_id] = self._dist_path.joinpath(js_module)
        self._smid_components[sub_module_id] = dict()

    def register_component(self,
                           sub_module_id: int,
                           component_name: str, registry_key) -> None:
        """
        Register a component.
        :param sub_module_id: ID of the sub-module
        :param component_name: Name of the ts-component-class
        :param registry_key: registry key for the component
        """
        if sub_module_id not in self._js_modules:
            raise ValueError(f"Sub-module ID {sub_module_id} not registered.")
        if registry_key in self._smid_components[sub_module_id]:
            raise ValueError(f"Component {registry_key} already registered.")

        self._smid_components[sub_module_id][registry_key] = component_name

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

    def get_component(self, sub_module_id: int, key: str) -> WebComponent:
        """
        Get the URL and ts-class of a component.
        :param sub_module_id: ID of the sub-module
        :param key: registry key for the component
        :return: [URL, ts-class] of the component
        """
        return WebComponent(
            self.get_js_module_url(sub_module_id),
            self.get_component_class(sub_module_id, key)
        )
