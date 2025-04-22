from src.model.local_model.module_interface.sub_module \
    import SubModule, SubModuleType


class JobSubModule(SubModule):
    """
    Class for the job submodule interface.
    """

    def __init__(self, config_component_name: str):
        super().__init__(SubModuleType.JOB_PROCESSOR)
        self._config_component_name = config_component_name

    def get_config_component(self) -> str:
        pass
