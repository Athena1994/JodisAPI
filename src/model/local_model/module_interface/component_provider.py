

from os import path


class ComponentProvider:
    def __init__(self, base_path: str):
        self._base_path = base_path

        self._modules = dict()

        # self._module_path = dict()
        # self._module_version_path = dict()
        # self._component_path = dict()

    def register_module(self, module, path: str) -> None:
        """
        Register a module with its path.
        """
        self._modules[module] = {'path': path, 'versions': dict()}

    def register_module_version(self,
                                module: str, version: str,
                                rel_path: str) -> None:
        """
        Register a module version with its path.
        """
        if module not in self._modules:
            raise ValueError(f"Module {module} not registered.")

        if version in self._modules[module]['versions']:
            raise ValueError(f"Version {version} already registered.")

        self._modules[module]['versions'][version] = {
            "path": path.join(self._modules[module]['path'], version, rel_path),
            "components": dict()
        }

    def register_component(self,
                           m: str, v: str, component: str,
                           js_module: str) -> None:
        """
        Register a component with its path.
        """
        if m not in self._modules:
            raise ValueError(f"Module {m} not registered.")
        if v not in self._modules[m]['versions']:
            raise ValueError(f"Version {v} not registered.")
        if component in self._modules[m]['versions'][v]['components']:
            raise ValueError(f"Component {component} already registered.")

        self._modules[m]['versions'][v]['components'][component] \
            = path.join(self._modules[m]['versions'][v]['path'], js_module)

    def get_component_url(self,
                          m: str, v: str, c: str) -> str:
        """
        Get the URL of a component.
        """
        if m not in self._modules:
            raise ValueError(f"Module {m} not registered.")
        if v not in self._modules[m]['versions']:
            raise ValueError(f"Version {v} not registered.")
        if c not in self._modules[m]['versions'][v]['components']:
            raise ValueError(f"Component {c} not registered.")
        return self._modules[m]['versions'][v]['components'][c]
