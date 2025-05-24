import logging
from typing import Optional
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from jodiscore.exceptions.invalid_state_error import InvalidStateError
from model.client import Client
from model.job import Job
from model.job_schedule_entry import JobScheduleEntry


class ClientManager:
    def __init__(self, session: Session, id: int, load_model: bool = False):
        self._id = id
        self._session = session

        self._model = None
        if load_model:
            self._model = self.model

    @staticmethod
    def create(session: Session, name: str) -> Client:
        logging.info(f"Creating client with name {name}")

        client = Client(name=name)
        session.add(client)
        return client

    @staticmethod
    def delete(session: Session, id: int) -> None:
        logging.info(f"Deleting client with id {id}")

        client = ClientManager(session, id, True)

        if client.get_active_job() is not None:
            raise InvalidStateError("Client has an active job")

        session.delete(client.model)

    @staticmethod
    def all(session: Session) -> list[Client]:
        logging.info("Fetching all clients")

        return session.execute(
            select(Client)
        ).scalars()

    @property
    def model(self) -> Client:
        if self._model is None:
            logging.info(f"Fetching client with id {self._id}")
            self._model = self._session.execute(
                select(Client).where(Client.id == self._id)
            ).scalar()

            if self._model is None:
                raise KeyError(f"Client with id {self._id} not found")

        return self._model

    def id(self) -> int:
        return self._id

    def is_in_state(self, state: Client.State) -> bool:
        return self.model.state == state

    def get_active_job(self) -> Optional[Job]:
        logging.info(f"Fetching active job for client {self._id}")
        return self._session.execute(
            select(Job)
            .where(
                and_(
                    Job.id.in_(
                      select(JobScheduleEntry.job_id)
                      .where(JobScheduleEntry.client_id == self._id)),
                    Job.sub_state == Job.SubState.RUNNING,
                    Job.state == Job.State.ASSIGNED
                )
            )
        ).scalar()
