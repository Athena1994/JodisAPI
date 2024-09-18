import logging
from typing import Optional
from sqlalchemy import and_, func, select, tuple_
from sqlalchemy.orm import Session

from db_model import models
from domain_model.exeptions import IndexValueError, StateError


class ClientManager:
    def __init__(self, session: Session, id: int, load_model: bool = False):
        self._id = id
        self._session = session

        self._model = None
        if load_model:
            self._model = self.model()

    @staticmethod
    def create(session: Session, name: str) -> models.Client:
        logging.info(f"Creating client with name {name}")

        client = models.Client(name=name)
        session.add(client)
        return client

    @staticmethod
    def delete(session: Session, id: int) -> None:
        logging.info(f"Deleting client with id {id}")

        client = ClientManager(session, id, True)

        if client.get_active_job() is not None:
            raise StateError("Client has an active job")

        session.delete(client.model())

    @staticmethod
    def all(session: Session) -> list[models.Client]:
        logging.info("Fetching all clients")

        return session.execute(
            select(models.Client)
        ).scalars()

    def model(self) -> models.Client:
        if self._model is None:
            logging.info(f"Fetching client with id {self._id}")
            self._model = self._session.execute(
                select(models.Client).where(models.Client.id == self._id)
            ).scalar()

            if self._model is None:
                raise IndexValueError(f"Client with id {self._id} not found")

        return self._model

    def get_id(self) -> int:
        return self._id

    def is_in_state(self, state: models.Client.State) -> bool:
        return self.model().state == state

    def get_active_job(self) -> Optional[models.Job]:
        logging.info(f"Fetching active job for client {self._id}")
        return self._session.execute(
            select(models.Job)
            .where(
                and_(
                    models.Job.id.in_(
                        select(models.JobScheduleEntry.job_id)
                        .where(models.JobScheduleEntry.client_id == self._id)),
                    models.Job.sub_state == models.Job.SubState.RUNNING
                )
            )
        ).scalar()

    def start_next_job(self) -> models.Job | None:

        logging.info(f"Starting next job for client {self._id}")

        if self.get_active_job() is not None:
            raise StateError("Client already has a running job")

        next_job = self._session.execute(
            select(models.Job)
            .where(models.Job.id.in_(
                select(models.JobScheduleEntry.job_id)
                .where(tuple_(models.JobScheduleEntry.client_id,
                              models.JobScheduleEntry.rank).in_(
                    select(models.JobScheduleEntry.client_id,
                           func.min(models.JobScheduleEntry.rank))
                    .where(models.JobScheduleEntry.client_id == self._id)
                    .group_by(models.JobScheduleEntry.client_id)
                ))
            ))
        ).scalar()

        if next_job is None:
            return None

        next_job.state = models.Job.State.ASSIGNED
        next_job.sub_state = models.Job.SubState.RUNNING

        new_session = next_job.session is None

        if new_session:
            next_job.session = models.JobSession(snapshot="undefined")

        return next_job
