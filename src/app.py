import json
import logging
from flask import Flask
from flask_cors import CORS
from flask_injector import FlaskInjector, singleton
from flask_socketio import SocketIO


from interface.socket.update_events.update_emitter import UpdateEmitter
from utils.db.db_context import DBContext
from interface.socket.connection_manager import ConnectionManager
from interface.socket.namespaces.client import ClientEventNamespace
from interface.http_endpoints.clients import clients_pb
from interface.http_endpoints.jobs import jobs_pb
from interface.socket.namespaces.update import UpdateEventNamespace


logging.basicConfig(level=logging.DEBUG)

PORT = 5000

with open('sql_test_cfg.json', 'r') as f:
    cfg = DBContext.Config.from_dict(json.load(f))


db = DBContext(cfg)
cm = ConnectionManager()
emitter = UpdateEmitter(db, cm)


def configure(binder):
    binder.bind(DBContext, to=db, scope=singleton)
    binder.bind(ConnectionManager, to=cm, scope=singleton)


app = Flask(__name__)
app.register_blueprint(clients_pb)
app.register_blueprint(jobs_pb)


CORS(app, resources={r"/*": {"origins": "*"}}, automatic_options=True)

socketio = SocketIO(app, cors_allowed_origins="*")
socketio.on_namespace(ClientEventNamespace(db, cm))
socketio.on_namespace(UpdateEventNamespace())


FlaskInjector(app=app, modules=[configure])

if __name__ == '__main__':
    socketio.run(app, use_reloader=True, debug=True, port=PORT)
