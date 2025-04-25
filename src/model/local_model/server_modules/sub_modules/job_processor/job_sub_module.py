

from dataclasses import dataclass
from model.local_model.server_modules.sub_modules.sub_module import SubModule
from model.local_model.server_modules.sub_modules.sub_module_types \
    import SubModuleTypes
from model.local_model.server_modules.utils.component_provider \
    import ComponentProvider
from model.local_model.server_modules.utils.web_component import WebComponent


class JobSubModule(SubModule):
    def __init__(self, id: int, cp: ComponentProvider, cfg: "Config"):
        super().__init__(id, SubModuleTypes.JOB_PROCESSOR, cp)

        cp.register_component(
            id, cfg.config_component, 'config-component')

    def get_config_component(self) -> WebComponent:
        return self.get_component('config-component')

    def validate_config(self, config: dict) -> bool:

    @dataclass
    class Config:
        config_component: str

        @staticmethod
        def from_dict(options: dict):
            if 'config-component' not in options:
                raise KeyError("Missing required field 'config-component'")
            return JobSubModule.Config(
                config_component=options['config-component']
            )
