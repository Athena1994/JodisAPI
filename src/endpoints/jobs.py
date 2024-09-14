

from dataclasses import dataclass
import logging
from flask import Blueprint, request
from injector import inject

from aithena.trading.config_loader import ConfigLoader
from server import Server


jobs_pb = Blueprint('jobs_pb', __name__)


@dataclass
class Job:
    id: int
    state: str
    sub_state: str
    client_id: int
    rank: int
    config: dict
    name: str
    description: str

    @staticmethod
    def from_db(job):
        client_id = (
            job.schedule_entry.client_id
            if job.schedule_entry is not None else -1
        )
        rank = job.schedule_entry.rank if job.schedule_entry is not None else -1

        return Job(id=job.id,
                   state=job.states[-1].state.value,
                   sub_state=job.states[-1].sub_state.value,
                   client_id=client_id,
                   rank=rank,
                   config=job.configuration,
                   name=job.name,
                   description=job.description)


@jobs_pb.route('/jobs', methods=['GET'])
@inject
def get_jobs(server: Server):
    all = len(request.args) == 0
    assigned = all or 'assigned' in request.args
    unassigned = all or 'unassigned' in request.args
    finished = all or 'finished' in request.args

    jobs = []
    with server.create_session() as session:
        for j in server.get_jobs(session,
                                 include_unassigned=unassigned,
                                 include_assigned=assigned,
                                 include_finished=finished):
            jobs.append(Job.from_db(j))

    return jobs


@jobs_pb.route('/job/validate', methods=['POST'])
@inject
def validate_config(server: Server):
    try:
        ConfigLoader(request.json)
        return {'valid': True}
    except ValueError as e:
        return {'valid': False, 'message': str(e)}


@jobs_pb.route('/jobs/delete', methods=['POST'])
@inject
def delete_jobs(server: Server):
    if 'ids' not in request.json:
        return {'error': 'Ids not provided'}, 400

    ids = request.json['ids']
    force = 'force' in request.json and request.json['force']

    if not all(isinstance(i, int) for i in ids):
        return {'error': 'Ids should be integers'}, 400

    deleted_ids = []
    with server.create_session() as session:
        for id in ids:
            try:
                server.delete_job(session, id, force)
                deleted_ids.append(id)
            except server.StateError or server.IndexValueError as e:
                logging.warning(f'Failed to delete job {id}: {str(e)}')
            except Exception as e:
                logging.error(f'Failed to delete job {id}: {str(e)}')

    server.emit_update('jobs-deleted', {'ids': deleted_ids})

    return {'deletedIds': deleted_ids}, 200


@jobs_pb.route('/job', methods=['POST'])
@inject
def create_job(server: Server):
    if 'name' not in request.json:
        logging.warning('Name not provided')
        return {'error': 'Name not provided'}, 400
    if 'config' not in request.json:
        logging.warning('config not provided')
        return {'error': 'Config not provided'}, 400
    if 'description' not in request.json:
        logging.warning('description not provided')
        return {'error': 'Description not provided'}, 400

    try:
        ConfigLoader(request.json['config'])
    except ValueError as e:
        logging.warning('Provided config is invalid')
        return {'error': f"Invalid config: {str(e)}"}, 400

    job_id = server.add_job(request.json['config'],
                            request.json['name'],
                            request.json['description'])

    with server.create_session() as session:
        job = Job.from_db(server.get_job(session, job_id))
        logging.info(f'Created job {job}')
        return [job], 201


@jobs_pb.route('/jobs/assign', methods=['POST'])
@inject
def assign_jobs(server: Server):
    if 'jobIds' not in request.json:
        return {'error': 'Ids not provided'}, 400
    if 'clientId' not in request.json:
        return {'error': 'Client id not provided'}, 400

    job_ids = request.json['jobIds']
    client_id = request.json['clientId']

    if not all(isinstance(i, int) for i in job_ids):
        return {'error': 'Job ids should be integers'}, 400
    if not isinstance(client_id, int):
        return {'error': 'Client id should be an integer'}, 400

    with server.create_session() as session:
        assigned_jobs = []
        for id in job_ids:
            try:
                updated_job = Job.from_db(
                    server.assign_job(session, id, client_id))
                assigned_jobs.append(updated_job)
            except server.StateError or server.IndexValueError as e:
                logging.warning(f'Failed to assign job {id}: {str(e)}')
            except Exception as e:
                logging.error(f'Failed to assign job {id}: {str(e)}')
                raise e

        session.commit()

        print(assigned_jobs)

        return assigned_jobs, 200


@jobs_pb.route('/jobs/unassign', methods=['POST'])
@inject
def unassign_jobs(server: Server):
    if 'jobIds' not in request.json:
        return {'error': 'Id not provided'}, 400

    job_ids = request.json['jobIds']

    force = 'force' in request.json and request.json['force']

    logging.info(f'Unassigning jobs {job_ids} (force={force})')

    if not all([isinstance(i, int) for i in job_ids]):
        return {'error': 'Job ids should be integers'}, 400

    jobs: list[Job] = []
    with server.create_session() as session:
        for job_id in job_ids:
            try:
                jobs.append(
                    Job.from_db(server.unassign_job(session, job_id, force)))
            except server.StateError or server.IndexValueError as e:
                logging.warning(f'Failed to unassign job {job_id}: {str(e)}')
            except Exception as e:
                logging.error(f'Failed to unassign job {job_id}: {str(e)}')
                raise e

        session.commit()

    for job in jobs:
        server.emit_update(
            'job-update', {
                'id': job.id,
                'updates': {
                    'state': job.state,
                    'subState': job.sub_state,
                    'clientId': job.client_id
                }
            }
        )

    return jobs, 200
