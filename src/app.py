import json
import logging
from flask import Flask
from flask_cors import CORS
from flask_injector import FlaskInjector, singleton
from flask_socketio import SocketIO


from interface.services.client_request_service import ClientRequestService
from interface.services.update_event_service import UpdateEventService
from interface.socket_namespaces.client import ClientEventNamespace
from interface.socket_namespaces.update import UpdateEventNamespace
from utils.db.db_context import DBContext
from interface.services.client_connection_service import ClientConnectionService
from interface.http_endpoints.clients import clients_pb
from interface.http_endpoints.jobs import jobs_pb
from utils.model_managing.subject_manager import SubjectManager


logging.basicConfig(level=logging.DEBUG)

PORT = 5000

with open('sql_test_cfg.json', 'r') as f:
    cfg = DBContext.Config.from_dict(json.load(f))


sm = SubjectManager()
db = DBContext(cfg)

ues = UpdateEventService(db, sm)
ccs = ClientConnectionService(sm)
crs = ClientRequestService(ccs)


def configure(binder):
    binder.bind(DBContext, to=db, scope=singleton)
    binder.bind(ClientConnectionService, to=ccs, scope=singleton)
    binder.bind(ClientRequestService, to=crs, scope=singleton)
    binder.bind(SubjectManager, to=sm, scope=singleton)


app = Flask(__name__)
app.register_blueprint(clients_pb)
app.register_blueprint(jobs_pb)


CORS(app, resources={r"/*": {"origins": "*"}}, automatic_options=True)

socketio = SocketIO(app, cors_allowed_origins="*")
socketio.on_namespace(ClientEventNamespace(db, ccs))
socketio.on_namespace(UpdateEventNamespace())


FlaskInjector(app=app, modules=[configure])

if __name__ == '__main__':
    socketio.run(app, use_reloader=True, debug=True, port=PORT)
