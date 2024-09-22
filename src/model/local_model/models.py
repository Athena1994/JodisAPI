

import enum

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
    ix = Attribute('ix', int, 0)
    count = Attribute('count', int, -1)
    time_per_ix = Attribute('time_per_ix', float, 0.)
    message = Attribute('message', str, '')
    estimated_times = Attribute('estimated_times', dict, {})
