import logging
from flask import request
from flask_socketio import Namespace

from server import Server


class ClientEventNamespace(Namespace):

    def __init__(self, name: str, server: Server):
        super().__init__(name)
        self._server = server
        print(type(server))

    def on_connect(self):
        logging.info(f'Socket with id {request.sid} connected')

    def on_disconnect(self):
        client_id = self._server.deregister_socket(request.sid)
        if client_id is not None:
            logging.info(f'Client {client_id} disconnected '
                         f'(socket {request.sid})')
        else:
            logging.info(f'Unassigned socket {request.sid} disconnected')

    def on_get_clients(self):
        logging.debug('Getting clients')
        with self._server.create_session() as session:
            clients = self._server.get_all_clients(session)
        self.emit('clients', [{'id': c.id, 'name': c.name} for c in clients])

    def on_claim_client(self, client_id: int):
        logging.debug(f'Claiming client {client_id}')
        if not isinstance(client_id, int):
            self.emit('error', {'message': 'Client id must be an integer'})
            logging.warning('Claim attempt with non-integer client id')
            return

        try:
            self._server.register_socket(request.sid, client_id)
            logging.info(f'Socket {request.sid} claimed client {client_id}')
            with self._server.create_session() as session:
                client = self._server.get_client(session, client_id)
                self.emit('claim_successfull',
                          {'id': client_id,
                           'name': client.name,
                           'state': client.state.value})
        except ValueError as e:
            logging.warning(f'Claim failed! {e}')
            self.emit('error', {'message': str(e)})

    def on_drop_claim(self):
        client_id = self._server.deregister_socket(request.sid)
        if client_id is not None:
            logging.info(f'Client {client_id} dropped claim '
                         f'(socket {request.sid})')
        else:
            logging.warning(f'Unassigned socket {request.sid} dropped claim')

    def on_set_state(self, active: bool):
        client_id = self._server.get_client_id(request.sid)
        if client_id is None:
            logging.warning(f'Attempt to set state on unclaimed socket '
                            f'{request.sid}')
            self.emit('error', {'message': 'Socket is not claimed'})
            return

        target_state = 'ACTIVE' if active else 'SUSPENDED'

        logging.debug(f'Setting state of client {client_id} to {target_state}')
        with self._server.create_session() as session:
            client = self._server.get_client(session, client_id)
            client.state = target_state
            session.commit()

        self.emit('success', {'id': client_id, 'state': target_state})
