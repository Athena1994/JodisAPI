
from flask import Blueprint
from flask_injector import inject

from model.local_model.client_session_manager import ClientSessionManager
from interface.data_objects import ClientProgressDO
from jodisutils.model_managing.subject_manager import SubjectManager


progress_pb = Blueprint('progress', __name__)


@progress_pb.route('/progress', methods=['GET'])
@inject
def get_all(sm: SubjectManager):
    with sm.create_session() as ls:
        return [ClientProgressDO.create(c)
                for c in ClientSessionManager.all(ls)], 200
