

from dataclasses import dataclass
import enum

from model.local_model.server_modules.module_control import ModuleControl
from utils.model_managing.attribute import Attribute
from utils.model_managing.subject import Subject


class ClientSession(Subject):
    class Phase(enum.Enum):
        PREPARATION = 'PREPARATION'
        TRAINING = 'TRAINING'
        VALIDATION = 'VALIDATION'
        FINALIZING = 'FINALIZING'

    client_id = Attribute('client_id', int, primary_key=True)
    phase = Attribute('phase', Phase, Phase.PREPARATION)
    phase_ix = Attribute('ix', int, 0)
    phase_count = Attribute('count', int, -1)
    time_per_ix = Attribute('time_per_ix', float, -1.)
    message = Attribute('message', str, '')


@dataclass
class ModuleError(BaseException):
    class Type(enum.Enum):
        PATH_NOT_FOUND = 0x01
        CFG_INVALID = 0x02
        UNKNOWN = 0x03
        CFG_MISSING = 0x04

    name: str
    description: str
    code: int = -1

    def __str__(self):
        return f"{self.name}({self.code}): {self.description}"


class ServerModule(Subject):
    id = Attribute('id', int, primary_key=True, auto_uid=True)

    version = Attribute('version', str)
    name = Attribute('name', str)

    description = Attribute('description', str, 'No description provided')

    control = Attribute('control', ModuleControl, None, True)

    error = Attribute('error', ModuleError, None, True)
