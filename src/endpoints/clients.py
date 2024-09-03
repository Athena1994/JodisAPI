
from dataclasses import dataclass
import json
import logging

from flask import Blueprint, request
from flask_injector import inject

from server import Server
from models import ClientConnectionState as CCS


clients_pb = Blueprint('clients', __name__)


@dataclass
class Client:
    id: int
    name: str
    connected: bool
    jobIds: list[int]


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


@clients_pb.route('/clients', methods=['GET'])
@inject
def get_clients(server: Server):
    clients = []
    with server.create_session() as session:
        for c in server.get_all_clients(session):
            is_connected = \
                c.connection_states[-1].state.value == CCS.State.CONNECTED.value

            clients.append(Client(
                jobIds=[j.job.id for j in c.schedule],
                id=c.id,
                name=c.name,
                connected=is_connected))

    return clients
