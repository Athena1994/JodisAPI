

import enum

from interface.socket.update_events.update_emitter import UpdateEmitter


class ActiveSession:
    class Phase(enum.Enum):
        PREPARATION = 'PREPARATION'
        TRAINING = 'TRAINING'
        VALIDATION = 'VALIDATION'
        FINALIZING = 'FINALIZING'

    def __init__(self, session_id: int):
        self._phase = ActiveSession.Phase.PREPARATION
        self._ix = 0
        self._count = -1
        self._time_per_ix = 0
        self._session_id = session_id

    def set_phase(self, phase: Phase, cnt: int):
        self._phase = phase
        self._ix = -1
        self._count = cnt

        UpdateEmitter.emit_update_event('session', self._session_id, {
            'phase': self._phase.value,
            'ix': self._ix,
            'count': self._count,
        })

    def update_progress(self, ix: int, time_per_ix: float):
        self._ix = ix
        self._time_per_ix = time_per_ix

        UpdateEmitter.emit_update_event('session', self._session_id, {
            'ix': ix,
            'time_per_ix': time_per_ix
        })

    def get_data(self) -> dict:
        return {
            'phase': self._phase.value,
            'ix': self._ix,
            'count': self._count,
            'time_per_ix': self._time_per_ix
        }
