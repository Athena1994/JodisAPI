
import logging

from flask import Blueprint
from flask_injector import inject

from interface.utils import bad_request, internal_server_error, ok
from model.exeptions import IndexValueError
from interface.services.client_request_service import ClientRequestService
from utils.db.db_context import DBContext
from services.client_connection_service import ClientConnectionService
from model.db_model.client_manager import ClientManager
from interface.data_objects import ClientDO
from utils.http_utils import Param, get_request_parameters


clients_pb = Blueprint('clients', __name__)


@clients_pb.route('/client/register', methods=['POST'])
@inject
def register_client(db: DBContext):
    try:
        name,    = get_request_parameters(Param('name', type_=str))
    except ValueError as e:
        return bad_request(str(e))

    logging.info("Registering client with name {name}")

    try:
        with db.create_session() as session:
            client = ClientManager.create(session, name)
            session.commit()
            id = client.id
    except Exception as e:
        return internal_server_error(e)

    logging.info(f"Client registered with id {id}")

    return ok('client registered', {'id': id})


@clients_pb.route('/client/delete', methods=['POST'])
@inject
def delete_client(db: DBContext):
    try:
        client_id, = get_request_parameters(Param('clientId', type_=int))
    except ValueError as e:
        return bad_request(str(e))

    logging.info(f"Deleting client with id {client_id}")

    try:
        with db.create_session() as session:
            ClientManager.delete(session, client_id)
            session.commit()
    except Exception as e:
        return internal_server_error(e)

    return ok('Client deleted')


@clients_pb.route('/client/request', methods=['POST'])
@inject
def server_request(rs: ClientRequestService, db: DBContext):
    logging.info("Client request received")
    try:
        client_id, cmd, args = get_request_parameters(
            Param('clientId', type_=int),
            Param('cmd', type_=str),
            Param('args', type_=dict))
    except ValueError as e:
        return bad_request(str(e))

    logging.info(f"client_id: {client_id}, request: {cmd}, args: {args}")

    with db.create_session() as session:
        try:
            client = ClientManager(session, client_id, True)
        except IndexValueError:
            return bad_request(f'ClientId {client_id} not found')

        try:
            rs.handle_request(client, cmd, args)
            return ok(f'request {cmd} passed on to client {client_id}')

        except Exception as e:
            return internal_server_error(e)


@clients_pb.route('/clients', methods=['GET'])
@inject
def get_clients(db: DBContext, cm: ClientConnectionService):
    with db.create_session() as session:
        return [
            ClientDO(
                id=c.id,
                name=c.name,
                state=c.state.value,
                connected=True
            ) for c in ClientManager.all(session)
        ], 200
