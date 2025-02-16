from datetime import datetime
import json
import logging
import os
from flask import Flask
from flask_cors import CORS
from flask_injector import FlaskInjector
from flask_socketio import SocketIO


from interface.socket_namespaces.client import ClientEventNamespace
from interface.socket_namespaces.update import UpdateEventNamespace
import services
from interface.http_endpoints.clients import clients_pb
from interface.http_endpoints.jobs import jobs_pb
from interface.http_endpoints.progress import progress_pb
from interface.http_endpoints.meta import meta_pb

import sys


def main(args: list):

    print("server startup...")

    cfg = parse_args(args)
    print(f'working dir: {os.getcwd()}')

    init_logging(cfg)

    services.init(cfg)

    app = init_flask_app()
    socketio = init_socket_io(app)

    port = cfg['server'].get('port', 5000)
    logging.info(f"starting server... (PORT: {port})")
    socketio.run(app,
                 use_reloader=True, debug=True,
                 port=port)


def parse_args(args: list) -> dict:
    if len(args) < 2:
        print("Usage: python app.py <config_file>")
        sys.exit(1)

    cfg_file = sys.argv[1]
    print(f"config file: {cfg_file}")

    cfg = json.load(open(cfg_file))

    return cfg


def init_logging(cfg: dict):
    log_cfg = cfg.get('logging', {})
    log_path = os.path.join(cfg['server']['root'],
                            log_cfg.get('log_path', 'logs'))
    use_file = log_cfg.get('use_file', False)
    use_stdout = log_cfg.get('use_stdout', True)
    log_level = log_cfg.get('verbosity', 'DEBUG')
    format = log_cfg.get('format', "%(asctime)s [%(threadName)-12.12s] "
                                   "[%(levelname)-5.5s]  %(message)s")

    print("initialize logging...")
    print(f"\t-use file: {use_file}")
    if use_file:
        print(f"\t-log path: {log_path}")
    print(f"\t-use stdout: {use_stdout}")
    print(f"\t-verbosity: {log_level}")

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    logFormatter = logging.Formatter(format)
    rootLogger = logging.getLogger()

    if use_file:
        fileHandler = logging.FileHandler(
            f"{log_path}/{datetime.now().strftime('%m-%d-%Y')}.log")
        fileHandler.setFormatter(logFormatter)
        rootLogger.addHandler(fileHandler)

    if use_stdout:
        consoleHandler = logging.StreamHandler()
        consoleHandler.setFormatter(logFormatter)
        rootLogger.addHandler(consoleHandler)

    rootLogger.setLevel(log_level)


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
