import json
import logging
from flask import Flask
from flask_cors import CORS
from flask_injector import FlaskInjector, singleton
from flask_socketio import SocketIO

from server import Server
from socket_namespaces import ClientEventNamespace
from endpoints.clients import clients_pb
from endpoints.jobs import jobs_pb


logging.basicConfig(level=logging.INFO)

PORT = 5000

with open('sql_test_cfg.json', 'r') as f:
    cfg = Server.Config.from_dict(json.load(f))

server = Server(cfg)


def configure(binder):
    binder.bind(Server, to=server, scope=singleton)


app = Flask(__name__)
app.register_blueprint(clients_pb)
app.register_blueprint(jobs_pb)

CORS(app)

socketio = SocketIO(app)
socketio.on_namespace(ClientEventNamespace('/client', server))

FlaskInjector(app=app, modules=[configure])

if __name__ == '__main__':
    socketio.run(app, use_reloader=True, debug=True, port=PORT)
