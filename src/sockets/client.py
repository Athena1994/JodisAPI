
import logging
from flask import request
from flask_socketio import Namespace

from jodiscore.exceptions.invalid_state_error import InvalidStateError
from model.manager.client_manager import ClientManager
from services.client_connection_service \
    import ClientConnectionService, NotConnectedError
from jodisutils.db.db_context import DBContext
from jodisutils.socket_utils import error, success
from jodisutils.injector import inject


class ClientEventNamespace(Namespace):

    def __init__(self):
        super().__init__('/client')

    # --- connection event handlers ---

    def on_connect(self):
        logging.info(f'Socket with id {request.sid} connected')

    @inject
    def on_disconnect(self, ccs: ClientConnectionService):
        logging.info(f'socket {request.sid} disconnected')

        if not ccs.has_sid(request.sid):
            return

        client_id = ccs.remove_by_sid(request.sid)
        logging.info(f'Client {client_id} disconnected!')

    # --- client claim handlers ---

    @inject
    def _drop_claim(self, sid: int, ccs: ClientConnectionService) -> bool:
        try:
            client_id = ccs.remove_by_sid(sid)
            logging.info(f'Claim on client {client_id} dropped '
                         f'(socket {request.sid})')
            return True

        except NotConnectedError:
            return False

    def on_drop_claim(self):
        if not self._drop_claim(request.sid):
            logging.warning(f'Unassigned socket {request.sid} tried to drop'
                            ' claim')

    @inject
    def on_claim_client(self, client_id: int,
                        db: DBContext, ccs: ClientConnectionService):

        logging.debug(f'Claiming client {client_id}')
        if not isinstance(client_id, int):
            return error(self, 'Client id must be an integer')

        try:
            with db.create_session() as session:
                client = ClientManager(session, client_id).model()

            ccs.add(request.sid, client_id)
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

    @inject
    def on_get_clients(self, db: DBContext):
        logging.debug('Getting clients')
        with db.create_session() as session:
            clients = ClientManager.all(session)
            self.emit('clients',
                      [{'id': c.id, 'name': c.name} for c in clients])

    @inject
    def on_set_state(self, active: bool,
                     ccs: ClientConnectionService, db: DBContext):

        try:
            client_id = ccs.get_cid(request.sid)
        except NotConnectedError:
            return error(self, 'Socket is not claimed')

        target_state = 'ACTIVE' if active else 'SUSPENDED'

        logging.debug(f'Setting state of client {client_id} to {target_state}')

        try:
            with db.create_session() as session:
                client = ClientManager(session, client_id).model()
                client.state = target_state
                session.commit()
            success(self, data={'id': client_id, 'state': target_state})
        except Exception as e:
            error(self, str(e))

    @inject
    def on_get_active_job(self,
                          ccs: ClientConnectionService, db: DBContext):
        try:
            client_id = ccs.get_cid(request.sid)
        except NotConnectedError:
            return error(self, 'socket not claimed')

        logging.debug(f'Client {client_id} requesting active job')
        try:
            with db.create_session() as session:
                job = ClientManager(session, client_id).get_active_job()
            if job is None:
                return error(self, 'No active job')
            success(self, data={'id': job.id})
        except Exception as e:
            error(self, str(e))

    @inject
    def on_claim_next_job(self,
                          ccs: ClientConnectionService, db: DBContext):
        try:
            client_id = ccs.get_cid(request.sid)
        except NotConnectedError:
            return error(self, 'socket is not claimed')

        logging.debug(f'Client {client_id} claiming next job')

        try:
            with db.create_session() as session:
                job = ClientManager(session, client_id).start_next_job()
                if job is None:
                    return error(self, "No jobs, available!")

                session.commit()

                success(self, 'job_claimed', {'id': job.id})

        except InvalidStateError as e:
            return error(self, {str(e)})
