
import logging
import traceback

from injector import Injector, inject

from services.server_modules.sub_modules.sub_module_factory\
     import SubModuleFactory

from services.server_modules.utils.error import Error
from services.server_modules.utils.state import State


class SubModuleControl:

    def __init__(self, json: dict,
                 sub_id: int,
                 sub_module_factory: SubModuleFactory):

        self._state = State.NOT_INITIALIZED
        self._error: Error = None
        self._sub_module = None

        try:
            self._sub_module = sub_module_factory.create(sub_id, json)
            self._state = State.INITIALIZED
        except Exception as e:
            self.error = Error(
                description=f"Failed to create sub-module: {e}",
                code=Error.Type.INITIALIZATION_FAILED,
                traceback=traceback.format_exc())
            return
    # --- methods -----------------------------------

    @inject
    def start(self, injector: Injector):
        if self._state != State.INITIALIZED:
            raise ValueError(f"Invalid State {self._state}: "
                             f"expected {State.INITIALIZED}")
        try:
            injector.call_with_injection(self._sub_module.start)
            self._state = State.READY
        except Exception:
            self.error = Error(
                "Failed to start sub module.",
                Error.Type.INTERNAL_ERROR,
                traceback=traceback.format_exc()
            )

    @inject
    def stop(self, injector: Injector):
        if self._state == State.INITIALIZED:
            raise ValueError(f"Invalid State {self._state}")
        try:
            injector.call_with_injection(self._sub_module.stop)
            self._state = State.INITIALIZED
        except Exception:
            self.error = Error(
                "Failed to stop sub module.",
                Error.Type.INTERNAL_ERROR,
                traceback=traceback.format_exc()
            )

    # --- properties -------------------------------

    @property
    def state(self) -> str:
        if self._error is not None:
            return State.ERROR
        if self._state == State.READY and self._sub_module.is_busy():
            return State.BUSY
        return self._state

    @property
    def error(self) -> Error:
        return self._error

    @error.setter
    def error(self, error: Error):
        self._error = error
        if error is not None:
            logging.warning(error)

    def __str__(self):
        if self._error is None:
            return f"({self._sub_module})"
        return f"(SubModule #{self._sub_id}, error)"
