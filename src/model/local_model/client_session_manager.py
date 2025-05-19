

import logging
from model.local_model import models
from jodisutils.model_managing.subject_session import SubjectSession


class ClientSessionManager:

    def __init__(self, session: SubjectSession, client_id: int):
        self._session = session
        self._model: models.ClientSession \
            = session.get(models.ClientSession, client_id, True)

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

    @staticmethod
    def exists(session: SubjectSession, client_id: int) -> bool:
        return session.exists(models.ClientSession, client_id)

    @staticmethod
    def all(session: SubjectSession) -> set[models.ClientSession]:
        return session.get_all(models.ClientSession)

    def change_phase(self, phase: models.ClientSession.Phase, cnt: int) -> None:
        self.model().phase = phase
        self.model().phase_ix = 0
        self.model().phase_count = cnt
        self.model().time_per_ix = -1.
        self.model().message = ''

    def update_phase(self, ix: int, time_per_ix: float) -> None:
        self.model().phase_ix = ix
        self.model().time_per_ix = time_per_ix

    def change_message(self, message: str) -> None:
        self.model().message = message
