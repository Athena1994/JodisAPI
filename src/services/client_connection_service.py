
from typing import Dict

import flask_socketio


class NotConnectedError(Exception):
    pass


class ClientConnectionService:
    def __init__(self):
        self._sid_to_cid: Dict[int, int] = {}
        self._cid_to_sid: Dict[int, int] = {}

    def add(self, sid: int, cid: int):
        if sid in self._sid_to_cid:
            raise ValueError(f"Socket {sid} already assigned to client")

        if cid in self._cid_to_sid:
            raise ValueError(f"Client {cid} already claimed")

        self._sid_to_cid[sid] = cid
        self._cid_to_sid[cid] = sid

    def remove_by_sid(self, sid: int) -> int:
        if sid not in self._sid_to_cid:
            raise NotConnectedError(
                f"No connection with socket id {sid} found")
        cid = self._sid_to_cid.pop(sid)

        return cid

    def remove_by_cid(self, cid: int) -> int:
        if cid not in self._cid_to_sid:
            raise NotConnectedError(
                f"No connection with client id {cid} found")
        sid = self._cid_to_sid.pop(cid)
        self._sid_to_cid.pop(sid)
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
