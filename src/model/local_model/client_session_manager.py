

from model.local_model import models
from utils.observable_model.subject_session import SubjectSession


class ClientSessionManager:

    def __init__(self, session: SubjectSession, client_id: int):
        self._session = session
        self._model = session.get(models.ClientSession, client_id, True)

    def model(self) -> models.ClientSession:
        return self._model

    @staticmethod
    def create(session: SubjectSession, client_id: int) -> models.ClientSession:
        return session.add(models.ClientSession(client_id=client_id))

    @staticmethod
    def delete(session: SubjectSession, client_id: int) -> None:
        s = ClientSessionManager(session, client_id).model()
        session.delete(s)


