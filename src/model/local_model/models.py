import enum

from services.server_modules.utils.error import Error
from services.server_modules.module_control import ModuleControl
from services.server_modules.utils.module_identifier import ModuleIdentifier
from jodisutils.model_managing.attribute import Attribute
from jodisutils.model_managing.subject import Subject


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


class ServerModule(Subject):
    id = Attribute('id', ModuleIdentifier, primary_key=True)

    description = Attribute('description', str, 'No description provided')

    control = Attribute('control', ModuleControl, None, True)

    error = Attribute('error', Error, None, True)

    def __str__(self):
        return f"(ServerModule: {self.id})"
