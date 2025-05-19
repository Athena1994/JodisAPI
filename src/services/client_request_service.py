
from jodiscore.exceptions.invalid_state_error import InvalidStateError
from model.client import Client
from model.manager.client_manager import ClientManager
from services.client_connection_service import ClientConnectionService


class ClientRequestService:
    def __init__(self,
                 connection_service: ClientConnectionService):
        self._cs = connection_service

    def handle_request(self, client: ClientManager, request: str, args):
        if request == 'change_state':
            self.request_client_state(client, args['active'])
        elif request == 'pause_job':
            self.request_pause_job(client)
        elif request == 'cancel_job':
            self.request_cancel_job(client)
        else:
            raise ValueError(f"Unknown request {request}")

    def request_client_state(self, client: ClientManager, active: bool):
        if active:
            self._cs.emit(client.id(), 'request_activation')
        else:
            self._cs.emit(client.id(), 'request_release')

    def request_pause_job(self, client: ClientManager):

        if not client.is_in_state(Client.State.SUSPENDED):
            raise InvalidStateError("Client must be suspended")

        self._cs.emit(client.id(), 'pause_job')

    def request_cancel_job(self, client: ClientManager):

        if not client.is_in_state(Client.State.SUSPENDED):
            raise InvalidStateError("Client must be suspended")

        self._cs.emit(client.id(), 'cancel_job')
