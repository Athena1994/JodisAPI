

import logging
from flask_socketio import Namespace


def success(ns: Namespace,
            event: str = "success",
            data: object = None,
            log: str = None):
    if log is not None:
        logging.info(log)
    ns.emit(event, data)


def error(ns: Namespace, msg: str):
    logging.warning(msg)
    ns.emit('error', {'message': msg})
