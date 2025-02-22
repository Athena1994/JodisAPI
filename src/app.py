from dataclasses import dataclass
from datetime import datetime
import json
import logging
import os
from flask import Flask
from flask_cors import CORS
from flask_injector import FlaskInjector
from flask_socketio import SocketIO


from app_config import AppConfig
import app_logger
from interface.socket_namespaces.client import ClientEventNamespace
from interface.socket_namespaces.update import UpdateEventNamespace
import services
from interface.http_endpoints.clients import clients_pb
from interface.http_endpoints.jobs import jobs_pb
from interface.http_endpoints.progress import progress_pb
from interface.http_endpoints.meta import meta_pb

import sys

from utils import path_builder


def main(args: list):

    print("server startup...")

    cfg = parse_args(args)
    print(f'working dir: {os.getcwd()}')

    path_builder.initialize(cfg.server.root)
    app_logger.initialize(cfg.logging)
    services.init(cfg)

    app = init_flask_app()
    socketio = init_socket_io(app)

    logging.info(f"starting server... (PORT: {cfg.server.port})")
    socketio.run(app,
                 use_reloader=True, debug=True,
                 port=cfg.server.port)


def parse_args(args: list) -> AppConfig:
    if len(args) < 2:
        print("Usage: python app.py <config_file>")
        sys.exit(1)

    cfg_file = sys.argv[1]

    if not os.path.exists(cfg_file):
        print(f"config file {cfg_file} not found")
        sys.exit(1)
    else:
        print(f"config file: {cfg_file}")

    return AppConfig.from_dict(json.load(open(cfg_file)))


def init_flask_app() -> Flask:
    app = Flask(__name__)

    app.register_blueprint(clients_pb)
    app.register_blueprint(jobs_pb)
    app.register_blueprint(progress_pb)
    app.register_blueprint(meta_pb)

    CORS(app, resources={r"/*": {"origins": "*"}}, automatic_options=True)
    FlaskInjector(app, modules=[services.flask_injector_configure])

    return app


def init_socket_io(app: Flask) -> SocketIO:
    socketio = SocketIO(app, cors_allowed_origins="*")
    socketio.on_namespace(ClientEventNamespace(services.get('db'),
                                               services.get('sm'),
                                               services.get('ccs')))
    socketio.on_namespace(UpdateEventNamespace())
    return socketio


if __name__ == '__main__':
    main(sys.argv)
