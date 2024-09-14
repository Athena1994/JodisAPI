
import logging
from flask import request
from flask_socketio import Namespace

from server import Server


class ClientEventNamespace(Namespace):

    def __init__(self, server: Server):
        super().__init__('/client')
        self._server = server

    def _emit_client_update(self, client_id: int, updates: dict):

        self.emit('client-changed',
                  {'id': client_id, 'updates': updates},
                  namespace='/update')

    # --- connection event handlers ---

    def on_connect(self):
        logging.info(f'Socket with id {request.sid} connected')

    def on_disconnect(self):
        self._drop_claim(request.sid)
        logging.info(f'socket {request.sid} disconnected')

    # --- client claim handlers ---

    def _drop_claim(self, sid: int) -> bool:
        client_id = self._server.deregister_socket(sid)
        if client_id is not None:
            logging.info(f'Claim on client {client_id} dropped '
                         f'(socket {request.sid})')
            self._emit_client_update(client_id, {'connected': False})
            return True
        return False

    def on_drop_claim(self):
        if not self._drop_claim(request.sid):
            logging.warning(f'Unassigned socket {request.sid} tried to drop'
                            ' claim')

    def on_claim_client(self, client_id: int):
        logging.debug(f'Claiming client {client_id}')
        if not isinstance(client_id, int):
            self.emit('error', {'message': 'Client id must be an integer'})
            logging.warning('Claim attempt with non-integer client id')
            return

        try:
            self._server.register_socket(request.sid, client_id)
            logging.info(f'Socket {request.sid} claimed client {client_id}')
            self._emit_client_update(client_id, {'connected': True})
            with self._server.create_session() as session:
                client = self._server.get_client(session, client_id)
                self.emit('claim_successfull',
                          {'id': client_id,
                           'name': client.name,
                           'state': client.state.value})

        except ValueError as e:
            logging.warning(f'Claim failed! {e}')
            self.emit('error', {'message': str(e)})

    # --- client event handlers ---

    def on_get_clients(self):
        logging.debug('Getting clients')
        with self._server.create_session() as session:
            clients = self._server.get_all_clients(session)
        self.emit('clients', [{'id': c.id, 'name': c.name} for c in clients])

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
        self._emit_client_update(client_id, {'state': target_state})

    def on_claim_next_job(self):
        client_id = self._server.get_client_id(request.sid)
        if client_id is None:
            logging.warning(f'Attempt to claim job on unclaimed socket '
                            f'{request.sid}')
            self.emit('error', {'message': 'Socket is not claimed'})
            return

        logging.debug(f'Client {client_id} claiming next job')
        with self._server.create_session() as session:
            try:
                job = self._server.start_next_job(session, client_id)
            except self._server.StateError as e:
                logging.warning(f'Failed to claim job: {str(e)}')
                self.emit('error', {'message': str(e)})
                return
            if job is None:
                self.emit('error', {'message': 'No jobs available'})
                return

            self.emit('job_claimed', {'id': job.id})
