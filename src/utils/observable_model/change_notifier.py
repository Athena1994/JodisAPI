

from abc import abstractmethod
import logging
from typing import Callable, Self


class ChangeEmitter:
    class Session:
        ChangeCallback = Callable[[Self, str, object], None]

        def __init__(self, listeners: dict[str, ChangeCallback]):
            self._listeners = listeners

        def __enter__(self):
            return self

        def __exit__(self, _, __, ___):
            self.flush()

        @abstractmethod
        def flush(self):
            pass

        def _notify(self, event: str, obj: object, value: dict):
            if '__tablename__' in obj.__dict__:
                type_ = obj.__tablename__
            else:
                type_ = str(type(obj))

            if type_ not in self._listeners:
                logging.debug(f'No listener for type {type_}')
                return

            self._listeners[type_](self, event, obj, value)

        def notify_add(self, obj: object):
            self._notify('add', obj, None)

        def notify_delete(self, obj: object):
            self._notify('delete', obj, None)

        def notify_update(self, obj: object, changes: dict):
            self._notify('update', obj, changes)

    def start_session(self,
                      listeners: dict[str, Session.ChangeCallback]) -> Session:
        pass


class ChangeNotifier:
    ChangeCallback = ChangeEmitter.Session.ChangeCallback

    class EmitterNotSetError(Exception):
        pass

    def __init__(self):
        self._listeners: dict[str, ChangeEmitter.Session.ChangeCallback] = {}
        self._emitter: ChangeEmitter = None

    def set_emitter(self, emitter: ChangeEmitter):
        self._emitter = emitter

    def add_listener(self, type_: str, listener: ChangeCallback):
        if type_ in self._listeners:
            raise Exception(f"listener for type {type_} already set")

        self._listeners[type_] = listener

    def begin_session(self) -> ChangeEmitter.Session:
        if not self._emitter:
            raise self.EmitterNotSetError('Emitter was not set yet!')

        return self._emitter.start_session(self._listeners)
