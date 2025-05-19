
import logging
import os
import sys
from pathlib import Path
from typing import Tuple
from flask import Flask
from flask_cors import CORS
from flask_injector import FlaskInjector
from flask_socketio import SocketIO
from injector import Injector

from app import app_config, app_constants, app_logger, app_services
from jodisutils.static_file_provider import StaticFileProvider
from sockets.client import ClientEventNamespace

from http_endpoints.clients import clients_pb
from http_endpoints.jobs import jobs_pb
from http_endpoints.meta import meta_pb
from http_endpoints.statics import statics_pb

from jodisutils.files import path_builder


def main(args: list):

    print("server startup...")

    parse_args(args)
    cfg = app_config.get()

    print(f'working dir: {os.getcwd()}')

    path_builder.initialize(cfg.server.root)
    path_builder.add_domain(app_constants.MODULE_DOMAIN, cfg.modules.path)
    app_logger.initialize(cfg.logging)
    app_services.init(cfg)

    app, injector = init_flask_app()
    socketio = init_socket_io(app)

    app_services.start(injector)

    logging.info(f"starting server... (PORT: {cfg.server.port})")
    socketio.run(app,
                 host=cfg.server.host,
                 use_reloader=True, debug=True,
                 port=cfg.server.port)


def parse_args(args: list) -> None:
    if len(args) < 2:
        print("Usage: python app.py <config_file>")
        sys.exit(1)

    try:
        app_config.initialize(Path(sys.argv[1]))
    except Exception as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)


def init_flask_app() -> Tuple[Flask, Injector]:
    app = Flask(__name__)

    app.register_blueprint(clients_pb)
    app.register_blueprint(jobs_pb)
    app.register_blueprint(meta_pb)
    app.register_blueprint(app_services.get(StaticFileProvider).blueprint)
    app.register_blueprint(statics_pb)

    CORS(app, resources={r"/*": {"origins": "*"}}, automatic_options=True)
    fi = FlaskInjector(app, modules=[app_services.flask_injector_configure])
    return app, fi.injector


def init_socket_io(app: Flask) -> SocketIO:
    socketio = SocketIO(app, cors_allowed_origins="*")
    socketio.on_namespace(ClientEventNamespace())
    return socketio


if __name__ == '__main__':
    main(sys.argv)
