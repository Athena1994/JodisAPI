
from abc import abstractmethod
import logging
from services.jobs.job_data import JobData
from services.server_modules.utils.module_identifier import ModuleIdentifier
from services.server_modules.utils.web_component import WebComponent


class JobProvider:

    def __init__(self, id: ModuleIdentifier):
        self._id = id

    # --- propeties ---

    @property
    def id(self) -> int:
        return self._id.id

    @property
    def name(self):
        return self._id.name

    @property
    def version(self):
        return self._id.version

    # --- abstract methods ---

    @property
    def src_hash(self) -> str:
        raise NotImplementedError()

    @property
    def config_component(self) -> WebComponent:
        raise NotImplementedError()

    @property
    def client_url(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def validate_config(self, cfg: dict) -> bool:
        raise NotImplementedError()

    @abstractmethod
    def create_job(self, cfg: dict) -> JobData:
        raise NotImplementedError()

    # --- public methods ---

    def is_compatible(self, client_version: str, hash: str) -> bool:
        """
        Check if the job provider is compatible with the given client version
        and hash.
        """
        if hash is not None and hash != "":
            local_hash = self.src_hash

            logging.debug(f"Checking hash identity for {self._id.name} "
                          f"({local_hash} vs {hash}) ")
            return local_hash == hash

        return self._id.version == client_version
