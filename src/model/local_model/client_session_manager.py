

import logging
from model.local_model import models
from utils.model_managing.subject_session import SubjectSession


class ClientSessionManager:

    def __init__(self, session: SubjectSession, client_id: int):
        self._session = session
        self._model = session.get(models.ClientSession, client_id, True)

    def model(self) -> models.ClientSession:
        return self._model

    @staticmethod
    def create(session: SubjectSession, client_id: int) -> models.ClientSession:
        logging.info(f"Creating ClientSession for client with id {client_id}")
        return session.add(models.ClientSession(client_id=client_id))

    @staticmethod
    def delete(session: SubjectSession, client_id: int) -> None:
        logging.info(f"Deleting ClientSession with client id {client_id}")
        s = ClientSessionManager(session, client_id).model()
        session.delete(s)
