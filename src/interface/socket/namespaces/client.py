
import logging
from flask import request
from flask_socketio import Namespace

from model.db_model.client_manager import ClientManager
from model.db_model.exeptions import StateError
from interface.socket.connection_manager import ConnectionManager
from utils.db.db_context import DBContext


class ClientEventNamespace(Namespace):

    def __init__(self, db: DBContext, cm: ConnectionManager):
        super().__init__('/client')
        self._db = db
        self._cm = cm

    # --- connection event handlers ---

    def on_connect(self):
        logging.info(f'Socket with id {request.sid} connected')

    def on_disconnect(self):
        self._drop_claim(request.sid)
        logging.info(f'socket {request.sid} disconnected')

    # --- client claim handlers ---

    def _drop_claim(self, sid: int) -> bool:
        client_id = self._cm.remove_connection(sid)
        if client_id is not None:
            logging.info(f'Claim on client {client_id} dropped '
                         f'(socket {request.sid})')
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
            with self._db.create_session() as session:
                client = ClientManager(session, client_id).model()

            self._cm.add_connection(request.sid, client_id)
            logging.info(f'Socket {request.sid} claimed client {client_id}')
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
        with self._db.create_session() as session:
            clients = ClientManager.all(session)
        self.emit('clients', [{'id': c.id, 'name': c.name} for c in clients])

    def on_set_state(self, active: bool):

        try:
            client_id = self._cm.get_connection_by_sid(request.sid).client_id()
        except ConnectionManager.ConnectionError:
            logging.warning(f'Attempt to set state on unclaimed socket '
                            f'{request.sid}')
            self.emit('error', {'message': 'Socket is not claimed'})
            return

        target_state = 'ACTIVE' if active else 'SUSPENDED'

        logging.debug(f'Setting state of client {client_id} to {target_state}')
        with self._db.create_session() as session:
            client = ClientManager(session, client_id).model()
            client.state = target_state
            session.commit()

        self.emit('success', {'id': client_id, 'state': target_state})

    def on_get_active_job(self):
        try:
            client_id = self._cm.get_connection_by_sid(request.sid).client_id()
        except ConnectionManager.ConnectionError:
            logging.warning(f'Attempt to get active job on  unclaimed socket '
                            f'{request.sid}')
            self.emit('error', {'message': 'Socket is not claimed'})
            return

        logging.debug(f'Client {client_id} requesting active job')
        with self._db.create_session() as session:
            job = ClientManager(session, client_id).get_active_job()
        if job is None:
            self.emit('error', {'message': 'No active job'})
            return

        self.emit('success', {'id': job.id})

    def on_claim_next_job(self):
        try:
            client_id = self._cm.get_connection_by_sid(request.sid).client_id()
        except ConnectionManager.ConnectionError:
            logging.warning(f'Attempt to claim job on  unclaimed socket '
                            f'{request.sid}')
            self.emit('error', {'message': 'Socket is not claimed'})
            return

        logging.debug(f'Client {client_id} claiming next job')
        with self._db.create_session() as session:
            try:
                job = ClientManager(session, client_id).start_next_job()
            except StateError as e:
                logging.warning(f'Failed to claim job: {str(e)}')
                self.emit('error', {'message': str(e)})
                return
            if job is None:
                self.emit('error', {'message': 'No jobs available'})
                return

            session.commit()

            self.emit('job_claimed', {'id': job.id})
