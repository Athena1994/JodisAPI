
from abc import abstractmethod
import abc
from dataclasses import dataclass

from utils.session.flushable_session import FlushableSession


@dataclass
class Update:
    id: int
    changes: dict


DeleteDict = dict[str, list[int]]
AddDict = dict[str, list[dict]]
UpdateDict = dict[str, dict[int, dict]]


class StagingSession(FlushableSession, abc.ABC):

    def __init__(self):
        super().__init__(commit_on_exit=True)

        self._staged_deletes: DeleteDict = {}
        self._staged_adds: AddDict = {}
        self._staged_updates: UpdateDict = {}

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

    def _clear(self):
        self._staged_adds.clear()
        self._staged_deletes.clear()
        self._staged_updates.clear()

    def _flush(self):
        self._flush_staged_data(self._staged_deletes,
                                self._staged_adds,
                                self._staged_updates)

    @abstractmethod
    def _flush_staged_data(self,
                           deletes: DeleteDict,
                           adds: AddDict,
                           updates: UpdateDict):
        pass
