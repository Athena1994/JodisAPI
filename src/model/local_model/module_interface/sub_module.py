
import enum


@enum
class SubModuleType(enum.Enum):
    """
    Enum for the different types of submodules.
    """
    JOB_PROCESSOR = 'job_processor'


class SubModule:
    """
    Class for the submodule interface.
    """

    def __init__(self, type: SubModuleType):
        self._type = type

    @property
    def type(self) -> SubModuleType:
        """
        Returns the type of the submodule.
        """
        return self._type
