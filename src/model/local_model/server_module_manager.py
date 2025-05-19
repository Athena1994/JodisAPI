

import logging
from model.local_model import models
from services.server_modules.module_control import ModuleControl
from utils.model_managing.subject_session import SubjectSession


class ServerModuleManager:

    def __init__(self, session: SubjectSession, id: str):
        self._session = session
        self._model: models.ServerModule \
            = session.get(models.ServerModule, id, True)

    def model(self) -> models.ServerModule:
        return self._model

    @staticmethod
    def create(session: SubjectSession, mc: ModuleControl) \
            -> models.ServerModule:
        if not mc.initialized:
            raise ValueError(f"Invalid module control config: {mc}")

        logging.info(f"Creating ServerModule for {mc}")
        return session.add(models.ServerModule(
            id=mc.id,
            description="",
            control=mc,
            error=mc.error
        ))

    @staticmethod
    def delete(session: SubjectSession, id: str) -> None:
        logging.info(f"Deleting ServerModule with id {id}")
        s = ServerModuleManager(session, id).model()
        session.delete(s)

    @staticmethod
    def exists(session: SubjectSession, id: str) -> bool:
        return session.exists(models.ServerModule, id)

    @staticmethod
    def get_all_ids(session: SubjectSession) -> set[str]:
        return {m.id for m in session.get_all(models.ServerModule)}

    @staticmethod
    def all(session: SubjectSession) -> set[models.ServerModule]:
        return session.get_all(models.ServerModule)
