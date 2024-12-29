
import logging

from flask import Blueprint
from flask_injector import inject

from interface.http_endpoints.http_utils\
      import bad_request, internal_server_error, ok
from model.exeptions import IndexValueError
from interface.services.client_request_service import ClientRequestService
from model.local_model.client_session_manager import ClientSessionManager
from utils.db.db_context import DBContext
from interface.services.client_connection_service import ClientConnectionService
from model.db_model.client_manager import ClientManager
from interface.data_objects import ClientDO, ClientProgressDO
from utils.http_utils import Param, get_request_parameters
from utils.model_managing.subject_manager import SubjectManager


progress_pb = Blueprint('progress', __name__)


@progress_pb.route('/progress', methods=['GET'])
@inject
def get_all(sm: SubjectManager):
    with sm.create_session() as ls:
        return [ClientProgressDO.create(c)
                for c in ClientSessionManager.all(ls)], 200
