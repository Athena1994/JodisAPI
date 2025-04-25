

from model.local_model.server_modules.utils.component_provider \
    import ComponentProvider
from model.local_model.server_modules.utils.web_component import WebComponent


class SubModule:

    def __init__(self, id: int, type: str,
                 cp: ComponentProvider):
        self._type = type
        self._id = id
        self._cp = cp

    def get_component(self, component: str) -> WebComponent:
        return self._cp.get_component(self._id, component)

    @property
    def cp(self) -> ComponentProvider:
        return self._cp

    def __str__(self):
        return f"SubModule#{self._id} ({self._type})"
