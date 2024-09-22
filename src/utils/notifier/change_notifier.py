

import logging
from typing import Callable

from utils.notifier.notification_session \
    import ChangeCallback, NotificationSession, KeyFn
from utils.session.flushable_session import FlushableSession

ContextSessionFactory = Callable[[], FlushableSession]


class FactoryNotSet(Exception):
    pass


class ChangeNotifier:

    def __init__(self):
        self._listeners: dict[str, ChangeCallback] = {}
        self._key_fns: dict[type, KeyFn] = {}
        self._context_session_factory: ContextSessionFactory = None

    def set_context_factory(self, callback: ContextSessionFactory):
        self._context_session_factory = callback

    def add_type_key_fn(self, type_: type, key_fn: KeyFn):
        self._key_fns[type_] = key_fn

    def add_listener(self, key: str, listener: ChangeCallback):
        if key in self._listeners:
            raise Exception(f"listener for key {key} already set")

        self._listeners[key] = listener

    def create_session(self) -> NotificationSession:
        if not self._context_session_factory:
            logging.warning('Context factory was not set yet!')
            return NotificationSession({}, {}, None)

        return NotificationSession(self._listeners, self._key_fns,
                                   self._context_session_factory())
