

from model.local_model.module_interface.sub_module \
    import SubModule, SubModuleType

from model.local_model.module_interface.job_sub_module import JobSubModule


def create(type: str, config: dict) -> SubModule:
    """
    Factory method to create a sub module of the given type.
    :param type: Type of the sub module.
    :param config: Configuration of the sub module.
    :return: Sub module of the given type.
    """
    if type == SubModuleType.JOB_PROCESSOR:
        return JobSubModule(config)
    else:
        raise ValueError(f"Unknown sub module type: {type}")
