

from injector import Injector
from services.server_modules.sub_modules.job_module.job_sub_module \
    import JobSubModule
from services.server_modules.sub_modules.sub_module import SubModule
from services.server_modules.sub_modules.sub_module_types\
    import SubModuleTypes
from services.server_modules.utils.js_component_provider \
    import JSComponentProvider
from services.server_modules.utils.module_identifier import ModuleIdentifier


class SubModuleFactory:
    def __init__(self, module_id: ModuleIdentifier,
                 cp: JSComponentProvider, injector: Injector):
        self._cp = cp

        self._injector = injector

        self._module_id = module_id

    def create(self, sub_id: int, json: dict) -> SubModule:
        cfg = SubModule.Config(**json)

        self._cp.register_sub_module(sub_id)

        if cfg.type == SubModuleTypes.JOB_MODULE.value:

            return self._injector.create_object(JobSubModule, {
                'module_id': self._module_id,
                'sub_id': sub_id,
                'cfg': JobSubModule.Config(**cfg.options)})

        else:
            raise ValueError(f"Unknown sub module type: {cfg.type}")
