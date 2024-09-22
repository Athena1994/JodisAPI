
import logging
from flask import request
from flask_socketio import Namespace

from model.db_model.client_manager import ClientManager
from model.exeptions import StateError
from interface.services.client_connection_service \
    import ClientConnectionService, NotConnectedError
from utils.db.db_context import DBContext
from interface.socket_namespaces.socket_utils import error, success


class ClientEventNamespace(Namespace):

    def __init__(self, db: DBContext, ccs: ClientConnectionService):
        super().__init__('/client')
        self._db = db
        self._ccs = ccs

    # --- connection event handlers ---

    def on_connect(self):
        logging.info(f'Socket with id {request.sid} connected')

    def on_disconnect(self):
        self._drop_claim(request.sid)
        logging.info(f'socket {request.sid} disconnected')

    # --- client claim handlers ---

    def _drop_claim(self, sid: int) -> bool:
        client_id = self._ccs.remove_by_sid(sid)
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
            return error(self, 'Client id must be an integer')

        try:
            with self._db.create_session() as session:
                client = ClientManager(session, client_id).model()

            self._ccs.add(request.sid, client_id)
            success(
                self, 'claim_successfull', {
                    'id': client_id,
                    'name': client.name,
                    'state': client.state.value
                }, f"Socket {request.sid} claimed client {client_id}"
            )

        except ValueError as e:
            error(self, f'Claim failed! {e}')

    # --- client event handlers ---

    def on_get_clients(self):
        logging.debug('Getting clients')
        with self._db.create_session() as session:
            clients = ClientManager.all(session)
            self.emit('clients',
                      [{'id': c.id, 'name': c.name} for c in clients])

    def on_set_state(self, active: bool):

        try:
            client_id = self._ccs.get_cid(request.sid)
        except NotConnectedError:
            return error(self, 'Socket is not claimed')

        target_state = 'ACTIVE' if active else 'SUSPENDED'

        logging.debug(f'Setting state of client {client_id} to {target_state}')

        try:
            with self._db.create_session() as session:
                client = ClientManager(session, client_id).model()
                client.state = target_state
                session.commit()
            success(self, data={'id': client_id, 'state': target_state})
        except Exception as e:
            error(self, str(e))

    def on_get_active_job(self):
        try:
            client_id = self._ccs.get_cid(request.sid)
        except NotConnectedError:
            return error(self, 'socket not claimed')

        logging.debug(f'Client {client_id} requesting active job')
        try:
            with self._db.create_session() as session:
                job = ClientManager(session, client_id).get_active_job()
            if job is None:
                return error(self, 'No active job')
            success(self, data={'id': job.id})
        except Exception as e:
            error(self, str(e))

    def on_claim_next_job(self):
        try:
            client_id = self._ccs.get_cid(request.sid)
        except NotConnectedError:
            return error(self, 'socket is not claimed')

        logging.debug(f'Client {client_id} claiming next job')

        try:
            with self._db.create_session() as session:
                job = ClientManager(session, client_id).start_next_job()
                if job is None:
                    return error(self, "No jobs, available!")

                session.commit()

                success(self, 'job_claimed', {'id': job.id})

        except StateError as e:
            return error(self, {str(e)})
