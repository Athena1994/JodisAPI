

import logging
from typing import Callable, Generic, TypeVar

from utils.session.flushable_session import FlushableSession


T = TypeVar('T', bound=FlushableSession)
ChangeCallback = Callable[[T, str, object], None]
KeyFn = Callable[[object], object]


class NotificationSession(FlushableSession, Generic[T]):

    def __init__(self,
                 listeners: dict[str, ChangeCallback],
                 key_fns: dict[type, KeyFn],
                 context: T):

        super().__init__(commit_on_exit=True)
        self._listeners = listeners
        self._key_fns = key_fns
        self._context = context

    def _notify(self, event: str, obj: object, value: dict):

        key_fn = self._key_fns.get(type(obj), lambda x: str(type(x)))

        listener_key = key_fn(obj)

        if listener_key not in self._listeners:
            logging.warning(f'No listener for type {type(obj)} '
                            f'(key {listener_key})')
            return

        self._listeners[listener_key](self._context, event, obj, value)

    def notify_add(self, obj: object):
        self._notify('add', obj, None)

    def notify_delete(self, obj: object):
        self._notify('delete', obj, None)

    def notify_update(self, obj: object, changes: dict):
        self._notify('update', obj, changes)

    def _flush(self):
        self._context.commit()
