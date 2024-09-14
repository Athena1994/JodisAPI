from dataclasses import dataclass
import logging
import flask_socketio
from sqlalchemy import and_, create_engine, func, or_, select, tuple_
from sqlalchemy.orm import Session

from src.models import (Base, Client, Job,
                        JobScheduleEntry, JobStatus)

from utils.config_utils import assert_fields_in_dict

JState = JobStatus.State
JSubState = JobStatus.SubState


class Server:

    class IndexValueError(ValueError):
        pass

    class StateError(ValueError):
        pass

    @dataclass
    class Config:
        sql_user: str
        sql_pw: str
        sql_server: str
        sql_db: str

        @staticmethod
        def from_dict(cfg: dict):
            assert_fields_in_dict(cfg, ['user', 'password', 'host', 'db'])
            return Server.Config(cfg['user'], cfg['password'],
                                 cfg['host'], cfg['db'])

        @staticmethod
        def get_test_config():
            return Server.Config("", "", "", "")

    def __init__(self, cfg: Config):
        if len(cfg.sql_user) == 0:
            credentials = '/'
        else:
            credentials = f"{cfg.sql_user}:{cfg.sql_pw}@"

        if len(cfg.sql_server) == 0:
            target = ':memory:'
        else:
            target = f"{cfg.sql_server}/{cfg.sql_db}"

        connect_query = f'mysql+pymysql://{credentials}{target}'
        self._engine = create_engine(connect_query)

        self._socket_to_client = {}
        self._client_to_socket = {}

    def emit_update(self, event: str, args: dict):
        flask_socketio.emit(event, args, namespace='/update', broadcast=True)

    def create_tables(self):
        Base.metadata.drop_all(self._engine)
        Base.metadata.create_all(self._engine)

    def create_session(self) -> Session:
        return Session(self._engine)

    # --- client management ---

    def add_client(self, name: str):
        client = Client(name=name)
        with Session(self._engine) as session:
            session.add(client)
            session.commit()
            return client.id

    def get_client(self, session: Session, client_id: int):
        client = session.execute(
            select(Client).where(Client.id == client_id)).scalar()

        return client

    def get_all_clients(self, session: Session):
        return session.execute(select(Client)).scalars().all()

    def get_client_id(self, socket_id: int) -> int | None:
        return self._socket_to_client.get(socket_id)

    def is_client_connected(self, client: Client):
        return client.id in self._client_to_socket

    def get_running_job(self, session: Session, client_id: int) -> Job | None:

        return session.execute(
            select(Job)
            .where(
                and_(
                    Job.id.in_(
                        select(JobScheduleEntry.job_id)
                        .where(JobScheduleEntry.client_id == client_id)),
                    Job.id.in_(
                        select(JobStatus.job_id)
                        .where(
                            and_(
                                JobStatus.sub_state == JSubState.RUNNING,
                                tuple_(JobStatus.job_id,
                                       JobStatus.creation_timestamp).in_(
                                    select(
                                        JobStatus.job_id,
                                        func.max(JobStatus.creation_timestamp))
                                    .group_by(JobStatus.job_id)
                                )
                            )
                        )
                    )
                )
            )
        ).scalar()

    def start_next_job(self, session: Session, client_id: int) -> Job | None:

        if self.get_running_job(session, client_id) is not None:
            raise Server.StateError("Client already has a running job")

        next_job = session.execute(
            select(Job)
            .where(Job.id.in_(
                select(JobScheduleEntry.job_id)
                .where(tuple_(JobScheduleEntry.client_id,
                              JobScheduleEntry.rank).in_(
                    select(JobScheduleEntry.client_id,
                           func.min(JobScheduleEntry.rank))
                    .where(JobScheduleEntry.client_id == client_id)
                    .group_by(JobScheduleEntry.client_id)
                ))
            ))
        ).scalar()

        if next_job is None:
            return None

        next_job.states.append(JobStatus(
            state=JobStatus.State.ASSIGNED,
            sub_state=JobStatus.SubState.RUNNING))

        session.commit()

        self.emit_update('job-changed', {
            'id': next_job.id,
            'updates': {
                'state': next_job.states[-1].state.value,
                'sub_state': next_job.states[-1].sub_state.value
            }
        })

        return next_job

    def request_client_state(self, client: Client, active: bool):

        sid = self._client_to_socket.get(client.id)
        if sid is None:
            raise ValueError(f"Client {client.id} not connected)")

        if active:
            flask_socketio.emit('request_activation',
                                to=sid, namespace='/client')
        else:
            flask_socketio.emit('request_release',
                                to=sid, namespace='/client')

    def request_pause_job(self, client: Client):

        sid = self._client_to_socket.get(client.id)
        if sid is None:
            raise ValueError(f"Client {client.id} not connected)")

        if client.state != Client.State.SUSPENDED:
            raise Server.StateError("Client must be suspended")

        flask_socketio.emit('pause_job',
                            to=sid, namespace='/client')

    def request_cancel_job(self, client: Client):

        sid = self._client_to_socket.get(client.id)
        if sid is None:
            raise ValueError(f"Client {client.id} not connected)")

        if client.state != Client.State.SUSPENDED:
            raise Server.StateError("Client must be suspended")

        flask_socketio.emit('cancel_job',
                            to=sid, namespace='/client')

    # --- job management ---

    def get_jobs(self,
                 session: Session,
                 include_unassigned: bool,
                 include_finished: bool,
                 include_assigned: bool):
        most_recent_state_stmt = (
            select(JobStatus.job_id, JobStatus.state)
            .where(
                tuple_(JobStatus.job_id, JobStatus.creation_timestamp)
                .in_(
                    select(JobStatus.job_id,
                           func.max(JobStatus.creation_timestamp))
                    .group_by(JobStatus.job_id)))
        )

        jobs_stmt = (
            select(Job)
            .where(
                or_(
                    and_(include_unassigned,
                         tuple_(Job.id, JState.UNASSIGNED.value)
                         .in_(most_recent_state_stmt)),
                    and_(include_assigned,
                         tuple_(Job.id, JState.ASSIGNED.value)
                         .in_(most_recent_state_stmt)),
                    and_(include_finished,
                         tuple_(Job.id, JState.FINISHED.value)
                         .in_(most_recent_state_stmt))
                )
            )
        )
        result = session.execute(jobs_stmt).scalars()
        return result

    def get_job(self,
                session: Session,
                job_id: int):
        return session.execute(
            select(Job).where(Job.id == job_id)
        ).scalar()

    def add_job(self, job_config: dict, name: str, desc: str) -> int:
        with Session(self._engine) as session:
            job = Job(configuration=job_config,
                      name=name,
                      description=desc)
            session.add(job)
            session.commit()
            return job.id

    def delete_job(self, session: Session, job_id: int, force: bool):
        logging.info(f"Deleting job with id {job_id}")
        job = session.execute(select(Job).where(Job.id == job_id)).scalar()
        if job is None:
            raise Server.IndexValueError(f"Job with id {job_id} not found")

        if job.states[-1].sub_state == JSubState.RUNNING and not force:
            raise Server.StateError("Active jobs cannot be deleted.")

        session.delete(job)
        session.commit()

    def assign_job(self, session: Session, job_id: int, client_id: int):
        job = session.execute(select(Job).
                              where(Job.id == job_id)).scalar()
        if job is None:
            raise Server.IndexValueError(
                f"Job with id {job_id} not found")

        client = session.execute(select(Client).
                                 where(Client.id == client_id)).scalar()
        if client is None:
            raise Server.IndexValueError(
                f"Client with id {client_id} not found")

        if job.schedule_entry is not None:
            raise Server.StateError(
                "Job already assigned to a client")

        next_rank = 0 if len(client.schedule) == 0 \
            else client.schedule[-1].rank + 1

        job.schedule_entry = JobScheduleEntry(
            client_id=client_id,
            rank=next_rank)

        job.states.append(JobStatus(state=JobStatus.State.ASSIGNED,
                                    sub_state=JobStatus.SubState.SCHEDULED))

        return job

    def unassign_job(self, session: Session, job_id: int, force: bool):

        job = session.execute(select(Job).
                              where(Job.id == job_id)).scalar()
        if job is None:
            raise Server.IndexValueError(
                f"Job with id {job_id} not found")

        if job.schedule_entry is None:
            return

        if job.states[-1].sub_state == JobStatus.SubState.RUNNING and not force:
            raise Server.StateError(
                "Cannot unassign job that is running")

        job.schedule_entry = None
        job.states.append(JobStatus(
            state=JobStatus.State.UNASSIGNED,
            sub_state=JobStatus.SubState.CREATED))

        self.emit_update('job-changed', {
            'id': job.id,
            'updates': {
                'state': job.states[-1].state.value,
                'sub_state': job.states[-1].sub_state.value
            }
        })

        return job

    # --- socket management ---

    def register_socket(self, socket_id: int, client_id: int):
        if socket_id in self._socket_to_client:
            raise ValueError(f"Socket {socket_id} already registered")

        self._socket_to_client[socket_id] = client_id
        self._client_to_socket[client_id] = socket_id

    def deregister_socket(self, socket_id: int) -> int:
        if socket_id not in self._socket_to_client:
            return None

        client_id = self._socket_to_client[socket_id]

        del self._socket_to_client[socket_id]
        del self._client_to_socket[client_id]

        return client_id
