

import logging
from flask import Blueprint, request
from injector import inject

from aithena.trading.config_loader import ConfigLoader
from interface.http_endpoints.http_utils \
      import bad_request, internal_server_error, not_found, ok
from utils.db.db_context import DBContext
from model.exeptions import IndexValueError, StateError
from model.db_model.job_manager import JobManager
from interface.data_objects import JobDO, JobSessionDO
from utils.http_utils import Param, get_request_parameters


jobs_pb = Blueprint('jobs_pb', __name__)


@jobs_pb.route('/jobs', methods=['GET'])
@inject
def get_jobs(db: DBContext):
    with db.create_session() as session:
        return [JobDO.from_db(j) for j in JobManager.all(session)], 200


@jobs_pb.route('/job/validate', methods=['POST'])
@inject
def validate_config():
    try:
        ConfigLoader(request.json)
        return ok(data={'valid': True})
    except ValueError as e:
        return ok(str(e), {'valid': False})


@jobs_pb.route('/jobs/delete', methods=['POST'])
@inject
def delete_jobs(server: DBContext):

    try:
        ids, force = get_request_parameters(
            Param('ids', collection=True, type_=int),
            Param('force', flag=True))
    except ValueError as e:
        return bad_request(str(e))

    deleted_ids = []
    with server.create_session() as session:
        for id in ids:
            try:
                JobManager.delete(session, id, force)
                deleted_ids.append(id)
            except Exception as e:
                logging.error(f'Failed to delete job {id}: {str(e)}')
        session.commit()

    return ok('Jobs deleted', {'deletedIds': deleted_ids})


@jobs_pb.route('/job', methods=['POST'])
@inject
def create_job(db: DBContext):
    try:
        name, config, description = get_request_parameters(
            Param('name', type_=str),
            Param('config', type_=dict),
            Param('description', type_=str))
    except ValueError as e:
        return bad_request(str(e))

    try:
        ConfigLoader(request.json['config'])
    except ValueError as e:
        return bad_request(f'Provided config is invalid ({e})')
    except Exception as e:
        return internal_server_error(e)

    with db.create_session() as session:
        JobManager.create(session, config, name, description)
        session.commit()

    return ok('Job created')


@jobs_pb.route('/jobs/assign', methods=['POST'])
@inject
def assign_jobs(db: DBContext):

    try:
        job_ids, client_id = get_request_parameters(
            Param('jobIds', collection=True, type_=int),
            Param('clientId', type_=int)
        )
    except ValueError as e:
        return bad_request(str(e))

    with db.create_session() as session:
        for id in job_ids:
            try:
                JobManager(session, id).assign(client_id)
            except StateError or IndexValueError as e:
                logging.warning(f'Failed to assign job {id}: {str(e)}')
            except Exception as e:
                return internal_server_error(e)

        session.commit()

    return ok()


@jobs_pb.route('/jobs/unassign', methods=['POST'])
@inject
def unassign_jobs(db: DBContext):

    try:
        job_ids, force = get_request_parameters(
            Param('jobIds', collection=True, type_=int),
            Param('force', flag=True))
    except ValueError as e:
        return bad_request(str(e))

    logging.info(f'Unassigning jobs {job_ids} (force={force})')

    with db.create_session() as session:
        for job_id in job_ids:
            try:
                JobManager(session, job_id).unassign_job(force)
            except StateError or IndexValueError as e:
                logging.warning(f'Failed to unassign job {job_id}: {str(e)}')
            except Exception as e:
                return internal_server_error(e)

        session.commit()

    return ok()


@jobs_pb.route('/job/session', methods=['GET'])
@inject
def get_job_session(db: DBContext):

    try:
        job_id, = get_request_parameters(Param('jobId', type_=int))
    except ValueError as e:
        return bad_request(str(e))

    with db.create_session() as session:
        job = JobManager(session, job_id).model()

        if job.session is None:
            return not_found('specified job has not session')

        return JobSessionDO.from_db(job.session), 200
