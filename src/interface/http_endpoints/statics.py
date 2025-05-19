

import logging
from flask import Blueprint

from interface.http_endpoints.http_utils \
      import internal_server_error, not_found, ok
from services.static_file_service import StaticFileService
from utils.injector import inject


statics_pb = Blueprint('statics_pb', __name__)


@statics_pb.route('/statics/url/<string:file_key>', methods=['GET'])
@inject
def get_unassigned_jobs(file_key: str, sfs: StaticFileService):
    """
    Get a static file by its key.
    :param file_key: Key of the static file.
    :param sfs: StaticFileService instance.
    :return: Static file content or error message.
    """
    logging.info(f"Static file '{file_key}' requested")
    try:
        if not sfs.has_file(file_key):
            return not_found(f"Static file '{file_key}' not found")
        return ok(sfs.get_file_url(file_key))
    except Exception as e:
        return internal_server_error(e,
                                     f"Failed to get static file '{file_key}'")
