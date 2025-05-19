
import enum


class State(enum.Enum):
    NOT_INITIALIZED = 'NOT_INITIALIZED'  # module is not initialized
    INITIALIZED = 'INITIALIZED'  # module is not registered
    READY = 'WAITING'  # module is registered and waiting for clients
    BUSY = 'BUSY'  # at least one sub-module is busy
    ERROR = 'ERROR'
