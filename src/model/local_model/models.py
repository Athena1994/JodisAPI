

from dataclasses import dataclass
import enum
from typing import Dict

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

    name: str
    description: str
    code: int = -1

    def __str__(self):
        return f"{self.name}({self.code}): {self.description}"


class ServerModuleVersion(Subject):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    id = Attribute('id', int, primary_key=True, auto_uid=True)

    version = Attribute('version', str)

    base_path = Attribute('base_path', str)

    api_version = Attribute('api_version', str, '0.0.0')

    src_dir = Attribute('src_dir', str, 'src')
    working_dir = Attribute('working_dir', str, 'rt')

    running = Attribute('running', bool, False)

    initialized = Attribute('initialized', bool, False)
    last_validation_succeeded = Attribute('src_validated', bool, False)
    last_src_hash = Attribute('last_src_hash', str | None, None, True)

    error = Attribute('error', ModuleError | None, None, True)


class ServerModule(Subject):
    name = Attribute('name', str, primary_key=True)
    description = Attribute('description', str, 'No description provided')

    enabled = Attribute('enabled', bool, False)
    autostart = Attribute('autostart', bool, False)

    version_ids = Attribute('versions', dict)
    active_version = Attribute('active_version', str | None, None, True)

    error = Attribute('error', ModuleError | None, None, True)
