from model.local_model.module_interface.sub_module \
    import SubModule, SubModuleType


class JobSubModule(SubModule):
    """
    Class for the job submodule interface.
    """

    def __init__(self, config: dict):
        super().__init__(SubModuleType.JOB_PROCESSOR)
        self._component_cfg = config.get('config-component')


    def get_config_component_url(self) -> str:
        self._component_cfg
