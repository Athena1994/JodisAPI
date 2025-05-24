import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from jodiscore.exceptions.invalid_state_error import InvalidStateError
from model.job import Job
from model.job_schedule_entry import JobScheduleEntry
from model.job_data import JobData


class JobManager:

    def __init__(self, session: Session, id: int, load_model: bool = False):
        self._session = session
        self._id = id

        self._model = None

        if load_model:
            self.model

    @property
    def model(self) -> Job:

        if self._model is None:
            logging.debug(f"Fetching job with id {self._id}")
            self._model = self._session.execute(
                select(Job).where(Job.id == self._id)
            ).scalar()

            if self._model is None:
                raise KeyError(f"Job with id {self._id} not found")

        return self._model

    @staticmethod
    def create(session: Session, data: JobData, name: str) -> Job:
        logging.info("Creating job...")
        job = Job(data=data, name=name)
        session.add(job)
        return job

    @staticmethod
    def delete(session: Session, id: int, force: bool) -> None:
        logging.info(f"Deleting job with id {id}")

        job = JobManager(session, id, True).model

        if job.sub_state == job.SubState.RUNNING and not force:
            raise InvalidStateError("Active jobs cannot be deleted.")

        session.delete(job)

    @staticmethod
    def all(session: Session) -> list[Job]:
        logging.info("Fetching all jobs")
        return session.execute(select(Job)).scalars()

    @staticmethod
    def all_unassigned(session: Session) -> list[Job]:
        return session.execute(select(Job).where(
            Job.state == Job.State.UNASSIGNED
        )).scalars()

    @staticmethod
    def client_jobs(session: Session, client_id: int) -> list[Job]:
        return filter(
            lambda j: j.schedule_entry.client_id == client_id,
            session.execute(select(Job).where(
                Job.state == Job.State.ASSIGNED,
            )).scalars()
        )

    def assign(self, client_id: int) -> None:
        from model.manager.client_manager import ClientManager

        logging.info(f"Assigning job {self._id} to client {client_id}")

        job = self.model

        if job.state != job.State.UNASSIGNED:
            raise InvalidStateError("Job already assigned to a client")

        client = ClientManager(self._session, client_id).model

        next_rank = 0 if len(client.schedule) == 0 \
            else client.schedule[-1].rank + 1

        job.schedule_entry = JobScheduleEntry(
            client_id=client_id,
            rank=next_rank)
        job.state = job.State.ASSIGNED
        job.sub_state = job.SubState.SCHEDULED

    def unassign(self, force: bool) -> None:
        logging.info(f"Unassigning job {self._id}")
        job = self.model

        if job.schedule_entry is None:
            return

        if job.sub_state == job.SubState.RUNNING and not force:
            raise InvalidStateError("Cannot unassign active job!")

        self._session.delete(job.schedule_entry)
        job.state = job.State.UNASSIGNED
        job.sub_state = job.SubState.CREATED

    def mark_execution_failed(self) -> None:
        job = self.model
        logging.info(f"Marking {job} execution as failed!")

        if job.state != job.State.ASSIGNED:
            raise InvalidStateError("Job is not assigned to a client")
        job.sub_state = job.SubState.FAILED

    def mark_execution_aborted(self) -> None:
        job = self.model
        logging.info(f"Marking {job} execution as aborted!")

        if job.state != job.State.ASSIGNED:
            raise InvalidStateError("Job is not assigned to a client")
        job.sub_state = job.SubState.ABORTED

    def mark_as_finished(self, result_json: str, completed: bool) -> None:
        job = self.model

        job.state = job.State.FINISHED

        if completed:
            job.sub_state = job.SubState.COMPLETED
        else:
            job.sub_state = job.SubState.RETURNED
        logging.info(f"Marking {job} execution as finished ({job.sub_state})!")

        job.result = result_json
