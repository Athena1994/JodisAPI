

import logging
import flask_socketio

from utils.observable_model.change_notifier import ChangeEmitter


class EmissionSession(ChangeEmitter.Session):
    @staticmethod
    def _emit(event: str, args: dict):
        flask_socketio.emit(event, args, namespace='/update', broadcast=True)
        logging.debug(f'Emitted event {event} with args {args}')

    def __init__(self, listeners):
        super().__init__(listeners)

        self._staged_deletes: dict[str, list[int]] = {}
        self._staged_adds: dict[str, list[dict]] = {}
        self._staged_updates: dict[str, list[tuple[int, dict]]] = {}

    def stage_add(self, type_: str, obj: dict):
        if type_ not in self._staged_adds:
            self._staged_adds[type_] = []

        self._staged_adds[type_].append(obj)

    def stage_delete(self, type_: str, id: int):
        if type_ not in self._staged_deletes:
            self._staged_deletes[type_] = []

        self._staged_deletes[type_].append(id)

    def stage_update(self, type_: str, id: int, changes: dict):
        if type_ not in self._staged_updates:
            self._staged_updates[type_] = {}

        if id not in self._staged_updates[type_]:
            self._staged_updates[type_][id] = {}
        self._staged_updates[type_][id].update(changes)

    def flush(self):
        for type_, objects in self._staged_adds.items():
            self._emit(f'{type_}-added',
                       [o.__dict__ for o in objects])

        for type_, ids in self._staged_deletes.items():
            self._emit(f'{type_}-deleted', ids)

        for type_, updates in self._staged_updates.items():
            self._emit(f'{type_}-changed', [{
                'id': id,
                'updates': updates
            } for id, updates in updates.items()])
