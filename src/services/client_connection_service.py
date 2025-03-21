
from typing import Dict

import flask_socketio

from model.local_model.client_session_manager import ClientSessionManager
from utils.model_managing.subject_manager import SubjectManager


class NotConnectedError(Exception):
    pass


class ClientConnectionService:
    def __init__(self, sm: SubjectManager):
        self._sid_to_cid: Dict[int, int] = {}
        self._cid_to_sid: Dict[int, int] = {}

        self._sm = sm

    def is_connected(self, cid: int) -> bool:
        return cid in self._cid_to_sid

    def add(self, sid: int, cid: int):
        if sid in self._sid_to_cid:
            raise ValueError(f"Socket {sid} already assigned to client")

        if cid in self._cid_to_sid:
            raise ValueError(f"Client {cid} already claimed")

        self._sid_to_cid[sid] = cid
        self._cid_to_sid[cid] = sid

        with self._sm.create_session() as session:
            ClientSessionManager.create(session, cid)
            session.commit()

    def _remove(self, cid: int, sid: int):
        del self._sid_to_cid[sid]
        del self._cid_to_sid[cid]

        with self._sm.create_session() as session:
            ClientSessionManager.delete(session, cid)
            session.commit()

    def remove_by_sid(self, sid: int) -> int:
        cid = self._sid_to_cid.get(sid)
        if cid is None:
            raise NotConnectedError(
                f"No connection with socket id {sid} found")

        self._remove(cid, sid)
        return cid

    def remove_by_cid(self, cid: int) -> int:
        sid = self._cid_to_sid.get(cid)
        if sid is None:
            raise NotConnectedError(
                f"No connection with client id {cid} found")

        self._remove(cid, sid)
        return sid

    def get_cid(self, sid: int) -> int:
        if sid not in self._sid_to_cid:
            raise NotConnectedError()

        return self._sid_to_cid[sid]

    def get_sid(self, cid: int) -> int:
        if cid not in self._cid_to_sid:
            raise NotConnectedError()

        return self._cid_to_sid[cid]

    def emit(self, cid: int, event: str, *args):
        sid = self.get_sid(cid)
        flask_socketio.emit(event, args, to=sid, namespace='/client')
