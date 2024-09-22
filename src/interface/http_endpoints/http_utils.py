
import json
import logging
import traceback
from typing import Tuple


def internal_server_error(e: Exception, msg: str = None) -> Tuple[dict, int]:

    logging.error(f"{msg} ({e})\n" if msg is not None else f"{str(e)}\n"
                  f"{traceback.format_exc()}")
    return json.dumps({
        'status': 'error',
        'message': 'internal server error'}), 500


def bad_request(msg: str) -> Tuple[dict, int]:
    logging.info(f'bad request ({msg})')
    return json.dumps({
        'status': 'bad request',
        'message': msg}), 400


def not_found(msg: str) -> Tuple[dict, int]:
    logging.info(f'bad request ({msg})')
    return json.dumps({
        'status': 'not found',
        'message': msg}), 404


def ok(msg: str = None, data: dict = {}) -> Tuple[dict, int]:
    logging.info(f'ok ({msg})')
    response = (
        {'status': 'ok'}
        | data
        | ({} if msg is None else {'message': msg})
    )
    return json.dumps(response), 200
