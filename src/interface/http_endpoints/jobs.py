

import logging
from flask import Blueprint, request
from injector import inject

from aithena.trading.config_loader import ConfigLoader
from utils.db.db_context import DBContext
from domain_model.exeptions import IndexValueError, StateError
from domain_model.job_manager import JobManager
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
        return {'valid': True}
    except ValueError as e:
        return {'valid': False, 'message': str(e)}


@jobs_pb.route('/jobs/delete', methods=['POST'])
@inject
def delete_jobs(server: DBContext):

    try:
        ids, force = get_request_parameters(
            Param('ids', collection=True, type_=int),
            Param('force', flag=True))
    except ValueError as e:
        logging.warning(str(e))
        return {'error': str(e)}, 400

    deleted_ids = []
    with server.create_session() as session:
        for id in ids:
            try:
                JobManager.delete(session, id, force)
                deleted_ids.append(id)
            except Exception as e:
                logging.error(f'Failed to delete job {id}: {str(e)}')
        session.commit()

    return {'deletedIds': deleted_ids}, 200


@jobs_pb.route('/job', methods=['POST'])
@inject
def create_job(db: DBContext):
    try:
        name, config, description = get_request_parameters(
            Param('name', type_=str),
            Param('config', type_=dict),
            Param('description', type_=str))
    except ValueError as e:
        logging.warning(str(e))
        return {'error': str(e)}, 400

    try:
        ConfigLoader(request.json['config'])
    except ValueError as e:
        logging.warning('Provided config is invalid')
        return {'error': f"Invalid config: {str(e)}"}, 400

    with db.create_session() as session:
        JobManager.create(session, config, name, description)
        session.commit()
        return {'status': 'ok'}, 200


@jobs_pb.route('/jobs/assign', methods=['POST'])
@inject
def assign_jobs(db: DBContext):

    try:
        job_ids, client_id = get_request_parameters(
            Param('jobIds', collection=True, type_=int),
            Param('clientId', type_=int)
        )
    except ValueError as e:
        logging.warning(str(e))
        return {'error': str(e)}, 400

    with db.create_session() as session:
        for id in job_ids:
            try:
                JobManager(session, id).assign(client_id)
            except StateError or IndexValueError as e:
                logging.warning(f'Failed to assign job {id}: {str(e)}')
            except Exception as e:
                logging.error(f'Failed to assign job {id}: {str(e)}')
                raise e

        session.commit()

    return {'status': 'ok'}, 200


@jobs_pb.route('/jobs/unassign', methods=['POST'])
@inject
def unassign_jobs(db: DBContext):

    try:
        job_ids, force = get_request_parameters(
            Param('jobIds', collection=True, type_=int),
            Param('force', flag=True))
    except ValueError as e:
        logging.warning(str(e))
        return {'error': str(e)}, 400

    logging.info(f'Unassigning jobs {job_ids} (force={force})')

    with db.create_session() as session:
        for job_id in job_ids:
            try:
                JobManager(session, job_id).unassign_job(force)
            except StateError or IndexValueError as e:
                logging.warning(f'Failed to unassign job {job_id}: {str(e)}')
            except Exception as e:
                logging.error(f'Failed to unassign job {job_id}: {str(e)}')
                raise e

        session.commit()

    return {'status': 'ok'}, 200


@jobs_pb.route('/job/session', methods=['GET'])
@inject
def get_job_session(db: DBContext):

    job_id = get_request_parameters(Param('jobId', type_=int))

    with db.create_session() as session:
        job = JobManager(session, job_id).model()

        if job.session is None:
            return {'error': 'Job has no session'}, 404

        return JobSessionDO.from_db(job.session), 200
