import flask_socketio
from sqlalchemy.orm import Session
from db_model import models
from domain_model.exeptions import StateError
from domain_model.client_manager import ClientManager


class Connection:
    def __init__(self, sid: int, client_id: int):
        self._sid = sid
        self._client_id = client_id

    def _emit(self, event: str, *args):
        flask_socketio.emit(event, args, to=self._sid, namespace='/client')

    def client_id(self) -> int:
        return self._client_id

    def request_client_state(self, active: bool):
        if active:
            self._emit('request_activation')
        else:
            self._emit('request_release')

    def request_pause_job(self, session: Session):

        if not ClientManager(session, self._client_id).is_in_state(
                models.Client.State.SUSPENDED):
            raise StateError("Client must be suspended")

        self._emit('pause_job')

    def request_cancel_job(self, session: Session):

        if not ClientManager(session, self._client_id).is_in_state(
                models.Client.State.SUSPENDED):
            raise StateError("Client must be suspended")

        self._emit('cancel_job')
