
import json
from flask import Blueprint, request
from injector import inject

from utils.db.db_context import DBContext


sessions_pb = Blueprint('sessions_pb', __name__)


@sessions_pb.route('/session/epoch', methods=['POST'])
@inject
def add_epoch_to_session(server: DBContext):
    missing = [
        f for f in ['sessionId', 'timestamp_start', 'timestamp_end', 'result']
        if f not in request.json]
    if len(missing) != 0:
        return json.dumps({
            'status': 'error',
            'message': f'Missing parameters ({",".join(missing)})'}), 400

    sessionId = int(request.json['sessionId'])
    timestamp_start = request.json['timestamp_start']
    timestamp_end = request.json['timestamp_end']
    result = request.json['result']

    with server.create_session() as db_session:
        s = server.get_job_session(db_session, sessionId, True)
        server.add_epoch(s, timestamp_start, timestamp_end, result)
        db_session.commit()
