import logging
from sqlalchemy import select
from sqlalchemy.orm import Session

from model.db_model import models
from model.db_model.client_manager import ClientManager
from model.exeptions import StateError


class JobManager:

    def __init__(self, session: Session, id: int, load_model: bool = False):
        self._session = session
        self._id = id

        self._model = self.model if load_model else None

    def model(self) -> models.Job:
        return self._session.execute(
            select(models.Job).where(models.Job.id == self._id)
        ).scalar()

    @staticmethod
    def create(session: Session,
               job_config: dict, name: str, desc: str) -> int:
        logging.info(f"Creating job with name {name}")

        job = models.Job(configuration=job_config,
                         name=name,
                         description=desc)
        session.add(job)
        return job.id

    @staticmethod
    def delete(session: Session, id: int, force: bool) -> None:
        logging.info(f"Deleting job with id {id}")

        job = JobManager(session, id, True).model()

        if job.sub_state == job.SubState.RUNNING and not force:
            raise StateError("Active jobs cannot be deleted.")

        session.delete(job)

    @staticmethod
    def all(session: Session) -> list[models.Job]:
        logging.info("Fetching all jobs")
        return session.execute(select(models.Job)).scalars()

    def assign(self, client_id: int) -> None:
        logging.info(f"Assigning job {self._id} to client {client_id}")

        job = self.model()

        if job.schedule_entry is not None:
            raise StateError(
                "Job already assigned to a client")

        client = ClientManager(self._session, client_id, True).model()

        next_rank = 0 if len(client.schedule) == 0 \
            else client.schedule[-1].rank + 1

        job.schedule_entry = models.JobScheduleEntry(
            client_id=client_id,
            rank=next_rank)
        job.state = job.State.ASSIGNED
        job.sub_state = job.SubState.SCHEDULED

    def unassign_job(self, force: bool) -> None:
        logging.info(f"Unassigning job {self._id}")
        job = self.model()

        if job.schedule_entry is None:
            return

        if job.sub_state == job.SubState.RUNNING and not force:
            raise StateError("Cannot unassign active job!")

        self._session.delete(job.schedule_entry)
        job.state = job.State.UNASSIGNED
        job.sub_state = job.SubState.CREATED
