import json
import logging
from flask import Flask
from flask_cors import CORS
from flask_injector import FlaskInjector, singleton
from flask_socketio import SocketIO


from server import Server
from socket_namespaces.client import ClientEventNamespace
from endpoints.clients import clients_pb
from endpoints.jobs import jobs_pb
from socket_namespaces.update import UpdateEventNamespace


logging.basicConfig(level=logging.DEBUG)

PORT = 5000

with open('sql_test_cfg.json', 'r') as f:
    cfg = Server.Config.from_dict(json.load(f))

server = Server(cfg)


def configure(binder):
    binder.bind(Server, to=server, scope=singleton)


app = Flask(__name__)
app.register_blueprint(clients_pb)
app.register_blueprint(jobs_pb)


CORS(app, resources={r"/*": {"origins": "*"}}, automatic_options=True)

socketio = SocketIO(app, cors_allowed_origins="*")
socketio.on_namespace(ClientEventNamespace(server))
socketio.on_namespace(UpdateEventNamespace(server))


FlaskInjector(app=app, modules=[configure])

if __name__ == '__main__':
    socketio.run(app, use_reloader=True, debug=True, port=PORT)
