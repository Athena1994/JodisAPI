from dataclasses import dataclass


@dataclass
class WebComponent:
    module_url: str
    component_class: str
