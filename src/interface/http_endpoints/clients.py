
import json
import logging

from flask import Blueprint
from flask_injector import inject

from utils.db.db_context import DBContext
from interface.socket.connection_manager import ConnectionManager
from model.db_model.client_manager import ClientManager
from interface.data_objects import ClientDO
from utils.http_utils import Param, get_request_parameters


clients_pb = Blueprint('clients', __name__)


@clients_pb.route('/client/register', methods=['POST'])
@inject
def register_client(db: DBContext):
    try:
        name,    = get_request_parameters(Param('name', type_=str))
    except Exception as e:
        logging.warning(str(e))
        return json.dumps({
            'status': 'error',
            'message': str(e)}), 400

    logging.info("Registering client with name {name}")

    try:
        with db.create_session() as session:
            client = ClientManager.create(session, name)
            session.commit()
            id = client.id
    except Exception as e:
        logging.warning(str(e))
        return json.dumps({
            'status': 'error',
            'message': str(e)}), 400

    logging.info(f"Client registered with id {id}")
    return json.dumps({
        'status': 'ok',
        'message': 'Client registered',
        'id': id})


@clients_pb.route('/client/delete', methods=['POST'])
@inject
def delete_client(db: DBContext):
    try:
        client_id, = get_request_parameters(Param('clientId', type_=int))
    except Exception as e:
        logging.warning(str(e))
        return json.dumps({
            'status': 'error',
            'message': str(e)}), 400

    logging.info(f"Deleting client with id {client_id}")

    try:
        with db.create_session() as session:
            ClientManager.delete(session, client_id)
            session.commit()
    except Exception as e:
        logging.warning(str(e))
        return json.dumps({
            'status': 'error',
            'message': str(e)}), 400

    return json.dumps({
        'status': 'ok',
        'message': 'Client deleted'})


@clients_pb.route('/client/request', methods=['POST'])
@inject
def server_request(cm: ConnectionManager, db: DBContext):
    logging.info("Client request received")
    try:
        client_id, cmd, args = get_request_parameters(
            Param('clientId', type_=int),
            Param('cmd', type_=str),
            Param('args', type_=dict))
    except Exception as e:
        logging.warning(str(e))
        return json.dumps({
            'status': 'error',
            'message': str(e)}), 400

    if not cm.is_connected(client_id):
        return json.dumps({
            'status': 'error',
            'message': 'Client not connected'}), 400

    try:
        connection = cm.get_connection_by_cid(client_id)
        with db.create_session() as session:

            if cmd == 'change_state':
                connection.request_client_state(args['active'])
                msg = 'Client state change requested'
            elif cmd == 'pause_job':
                connection.request_pause_job(session)
                msg = 'Job pause requested'
            elif cmd == 'cancel_job':
                connection.request_cancel_job(session)
                msg = 'Job cancel requested'

            return json.dumps({
                'status': 'ok',
                'message': msg
            }), 200

    except Exception as e:
        logging.warning(str(e))
        return json.dumps({
            'status': 'error',
            'message': str(e)}), 400


@clients_pb.route('/clients', methods=['GET'])
@inject
def get_clients(db: DBContext, cm: ConnectionManager):
    with db.create_session() as session:
        return [
            ClientDO(
                id=c.id,
                name=c.name,
                state=c.state.value,
                connected=cm.is_connected(c.id)
            ) for c in ClientManager.all(session)
        ], 200
