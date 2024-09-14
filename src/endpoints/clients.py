
from dataclasses import dataclass
import json
import logging

from flask import Blueprint, request
from flask_injector import inject

from server import Server


clients_pb = Blueprint('clients', __name__)


@dataclass
class Client:
    id: int
    name: str
    connected: bool
    jobIds: list[int]
    state: str


@clients_pb.route('/client/register', methods=['POST'])
@inject
def register_client(server: Server):
    name = request.args.get('name')
    id = server.add_client(name)
    logging.info(f"Client registered with id {id}")
    return json.dumps({
        'status': 'ok',
        'message': 'Client registered',
        'id': id})


@clients_pb.route('/client/request', methods=['POST'])
@inject
def server_request(server: Server):
    if ('clientId' not in request.json
       or 'cmd' not in request.json
       or 'args' not in request.json):
        logging.warning('Missing parameters')
        return json.dumps({
            'status': 'error',
            'message': 'Missing parameters'}), 400

    id = int(request.json['clientId'])
    cmd = request.json['cmd']
    args = request.json['args']

    with server.create_session() as session:
        client = server.get_client(session, id)
        if client is None:
            return json.dumps({
                'status': 'error',
                'message': 'Client not found'}), 404

        if cmd == 'change_state':
            server.request_client_state(client, args['active'])
            msg = 'Client state change requested'
        elif cmd == 'pause_job':
            server.request_pause_job(client)
            msg = 'Job pause requested'
        elif cmd == 'cancel_job':
            server.request_cancel_job(client)
            msg = 'Job cancel requested'

        return json.dumps({
            'status': 'ok',
            'message': msg
        }), 200


@clients_pb.route('/clients', methods=['GET'])
@inject
def get_clients(server: Server):
    clients = []
    with server.create_session() as session:
        for c in server.get_all_clients(session):
            clients.append(Client(
                jobIds=[j.job.id for j in c.schedule],
                id=c.id,
                name=c.name,
                state=c.state.value,
                connected=server.is_client_connected(c))), 200

    return clients
