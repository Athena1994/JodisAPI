
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

@clients_pb.route('/client/request_state', methods=['POST'])
@inject
def request_client_state(server: Server):
    id = int(request.args.get('clientId'))
    active = request.args.get('active')

    server.request_client_state(id, active)

    with server.create_session() as session:
        client = server.get_client(session, id)
        return json.dumps({
            'status': 'ok',
            'message': 'Client state retrieved',
            'id': client.id,
            'name': client.name,
            'state': client.state.value})

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
                connected=server.is_client_connected(c)))

    return clients
