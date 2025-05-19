

import json
import logging
from flask import Blueprint, request
from injector import inject

from interface.http_endpoints.http_utils \
      import bad_request, internal_server_error, not_found, ok
from model.exeptions import StateError
from services.jobs.job_service import JobService
from utils.db.db_context import DBContext
from model.db_model.job_manager import JobManager
from interface.data_objects import JobDO, JobProviderDO, JobSessionDO
from utils.http_utils import (Param, get_request_parameters,
                              inject_query_parameters)
from utils.version import Version


jobs_pb = Blueprint('jobs_pb', __name__)


@jobs_pb.route('/jobs/unassigned', methods=['GET'])
@inject
def get_unassigned_jobs(db: DBContext):
    with db.create_session() as session:
        unassigned_jobs = [JobDO.from_db(j)
                           for j in JobManager.all_unassigned(session)]
        logging.info(f"Unassigned jobs requested -> {unassigned_jobs}")
        return unassigned_jobs, 200


@jobs_pb.route('/client/<int:client_id>/jobs', methods=['GET'])
@inject
def get_assigned_jobs(client_id: int, db: DBContext):
    with db.create_session() as session:
        return ([JobDO.from_db(j)
                 for j in JobManager.client_jobs(session, client_id)], 200)


@jobs_pb.route('/client/<int:client_id>/jobs/<int:job_id>', methods=['POST'])
@inject
def assign_job(client_id: int, job_id: int, js: JobService):
    logging.info(f'http-request: Assigning job {job_id} to client {client_id}')
    try:
        js.assign_job([job_id], client_id)
        return ok('Job assigned')
    except KeyError as e:
        return not_found(f'{str(e)}')
    except StateError as e:
        return bad_request(f'Job is not in the correct state: {str(e)}')
    except Exception as e:
        return bad_request(f'Failed to assign job: {str(e)}')


@jobs_pb.route('/jobs/meta/modules', methods=['GET'])
@inject
def get_modules(js: JobService):
    return ([JobProviderDO.create(p).to_json() for p in js.get_all_provider()],
            200)


@jobs_pb.route('/jobs/meta/module/<string:name>', methods=['GET'])
@inject
def get_versions(js: JobService, name: str):
    try:
        provider = sorted(js.get_provider_by_name(name),
                          key=lambda p: Version.parse(p.version).as_tuple(),
                          reverse=True)
    except KeyError as e:
        return not_found(f'Job provider not found: {str(e)}')

    return [JobProviderDO.create(p).to_json() for p in provider], 200


@jobs_pb.route('/jobs/meta/module/<int:id>', methods=['GET'])
@inject
def get_module(js: JobService, id: int):
    return json.dumps(JobProviderDO.create(js.get_provider(id)).__dict__), 200


@jobs_pb.route('/jobs/meta/compatibility', methods=['GET'])
@inject
@inject_query_parameters
def check_compatability(js: JobService,
                        module_id: int, client_version: str,
                        src_hash: str):

    logging.info(f"Checking compatibility for {module_id} {client_version} "
                 f"({src_hash})")

    try:
        comp = js.is_compatible(module_id, client_version, src_hash)
        return ok(comp, {'compatible': comp})
    except KeyError as e:
        return not_found(f'Job provider not found: {str(e)}')
    except ValueError as e:
        return bad_request(f'Invalid parameters: {str(e)}')


@jobs_pb.route('/jobs', methods=['GET'])
@inject
def get_jobs(db: DBContext):
    with db.create_session() as session:
        return [JobDO.from_db(j) for j in JobManager.all(session)], 200


@jobs_pb.route('/job/validate', methods=['POST'])
@inject
@inject_query_parameters
def validate_config(js: JobService, module_id: int):
    try:
        config = dict(request.json)
    except Exception as e:
        return bad_request(str(e))

    try:
        valid = js.validate_job(module_id, config)
        return ok(f"{valid}", {'valid': valid})
    except Exception as e:
        return internal_server_error(e)


@jobs_pb.route('/jobs/delete', methods=['POST'])
@inject
def delete_jobs(js: JobService):

    try:
        ids, force = get_request_parameters(
            Param('ids', collection=True, type_=int),
            Param('force', flag=True))
    except ValueError as e:
        return bad_request(str(e))

    deleted_ids = js.delete_jobs(ids, force)

    return ok('Jobs deleted', {'deletedIds': deleted_ids})


@jobs_pb.route('/job/<int:module_id>', methods=['POST'])
@inject
@inject_query_parameters
def create_job(js: JobService, module_id: int, name: str = None):
    """Create a new job with the given configuration."""

    logging.info(f'http-request: Creating job for module {module_id} ({name})')
    try:
        config = dict(request.json)
    except Exception as e:
        return bad_request(str(e))

    try:
        return ok(data=js.create_job(module_id, config, name).__dict__)
    except ValueError as e:
        return bad_request(f'Invalid parameters: {str(e)}')
    except Exception as e:
        return internal_server_error(f'Failed to create job: {str(e)}')


@jobs_pb.route('/jobs/assign', methods=['POST'])
@inject
def assign_jobs(js: JobService):

    try:
        job_ids, client_id = get_request_parameters(
            Param('jobIds', collection=True, type_=int),
            Param('clientId', type_=int)
        )
    except ValueError as e:
        return bad_request(str(e))

    try:
        js.assign_job(job_ids, client_id)
    except Exception:
        return bad_request('Failed to assign jobs')

    return ok()


@jobs_pb.route('/jobs/unassign/<int:job_id>', methods=['POST'])
@inject
@inject_query_parameters
def unassign_jobs(js: JobService, job_id: int, force: bool = False):
    logging.info(f'Unassigning job {job_id} (force={force})')
    try:
        js.unassign_job([job_id], force)
    except Exception as e:
        return bad_request(f'Failed to unassign jobs! {e}')

    return ok()


@jobs_pb.route('/jobs/start/<int:job_id>', methods=['POST'])
@inject
def start_job(js: JobService, job_id: int):
    logging.info(f'starting job {job_id})')
    try:
        js.start_job(job_id)
    except Exception as e:
        return bad_request(f'Failed to start jobs! {e}')

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
            return not_found('specified job has no session')

        return JobSessionDO.from_db(job.session), 200
