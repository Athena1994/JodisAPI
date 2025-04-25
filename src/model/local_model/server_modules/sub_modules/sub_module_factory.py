

from model.local_model.server_modules.sub_modules.job_processor.job_sub_module\
      import JobSubModule
from model.local_model.server_modules.sub_modules.sub_module import SubModule
from model.local_model.server_modules.sub_modules.sub_module_types\
      import SubModuleTypes
from model.local_model.server_modules.utils.component_provider \
    import ComponentProvider


class SubModuleFactory:
    def __init__(self, id: int, cp: ComponentProvider):
        self._cp = cp
        self._id = id

    def create(self, sub_module_type: str, options: dict) -> SubModule:
        if sub_module_type == SubModuleTypes.JOB_PROCESSOR.value:
            return JobSubModule(self._id, self._cp,
                                JobSubModule.Config.from_dict(options))
        else:
            raise ValueError(f"Unknown sub module type: {sub_module_type}")
