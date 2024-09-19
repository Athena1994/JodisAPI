
import logging
from interface.socket.connection import Connection
from typing import Dict

from utils.observable_model.change_notifier import ChangeNotifier


class ConnectionManager:
    class ConnectionError(Exception):
        pass

    def __init__(self):
        self._sid_to_cid: Dict[int, int] = {}
        self._connections: Dict[int, Connection] = {}
        self._notifier = ChangeNotifier()

    def get_notifier(self) -> ChangeNotifier:
        return self._notifier

    def is_connected(self, client_id: int) -> bool:
        return client_id in self._connections

    def add_connection(self, sid: int, client_id: int) -> None:
        logging.info(f"Adding connection with socket id {sid} "
                     f"to client {client_id}")
        if sid in self._sid_to_cid:
            raise ValueError(f"Socket {sid} already assigned to client")
        if client_id in self._connections:
            raise ValueError(f"Client {client_id} already claimed")

        self._sid_to_cid[sid] = client_id
        self._connections[client_id] = Connection(sid, client_id)

        with self._notifier.begin_session() as session:
            session.notify_add(self._connections[client_id])

    def remove_connection(self, sid: int) -> int | None:
        logging.info(f"Removing connection with socket id {sid}")
        client_id = self._sid_to_cid.get(sid)
        if client_id is None:
            return

        connection = self._connections[client_id]

        del self._sid_to_cid[sid]
        del self._connections[client_id]

        with self._notifier.begin_session() as session:
            session.notify_delete(connection)

        return client_id

    def get_connection_by_sid(self, sid: int) -> Connection:
        cid = self._sid_to_cid.get(sid)
        if cid is None:
            raise ConnectionManager.ConnectionError(
                f"No connection with socket id {sid} found")
        return self.get_connection_by_cid(cid)

    def get_connection_by_cid(self, client_id: int) -> Connection:

        c = self._connections.get(client_id)

        if c is None:
            raise ConnectionManager.ConnectionError(
                f"No connection with client id {client_id} found")

        return c
