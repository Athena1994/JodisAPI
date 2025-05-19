from __future__ import annotations

import logging
from typing import Dict, List
from model.db_model.client_manager import ClientManager
from model.db_model.job_manager import JobManager
from model.db_model.models import Job
from model.exeptions import StateError
from services.server_modules.utils.module_identifier import ModuleIdentifier
from services.server_modules.utils.web_component import WebComponent
from services.jobs.job_provider import JobProvider
from jodisutils.db.db_context import DBContext


class JobService:
    def __init__(self, db: DBContext):
        self._db = db

        self._provider: Dict[ModuleIdentifier, JobProvider] = {}

    def start_job(self, job_id: int) -> None:
        with self._db.create_session() as session:
            job = JobManager(session, job_id)
            job_model = job.model()
            if job_model.sub_state != Job.SubState.SCHEDULED:
                raise StateError("Job is not in SCHEDULED state")

            client = ClientManager(session,
                                   job_model.schedule_entry.client_id, True)
            if client.get_active_job() is not None:
                raise StateError("Client has an active job")

            job_model.sub_state = Job.SubState.RUNNING

            session.commit()

    def is_compatible(self,
                      module_id: int, client_version: str,
                      remote_hash: str) -> bool:
        if module_id not in self._provider:
            raise KeyError(f"Provider {module_id} not registered!")
        module = self._provider[module_id]
        return module.is_compatible(client_version, remote_hash)

    def register_provider(self,
                          module_id: ModuleIdentifier,
                          provider: JobProvider):
        if module_id in self._provider:
            raise ValueError(f"Provider {module_id} already registered")
        self._provider[module_id] = provider
        logging.info("Registered job provider %s", module_id)

    def unregister_provider(self, module_id: int):
        if module_id not in self._provider:
            raise KeyError(f"Provider {module_id} not registered!")
        del self._provider[module_id]

    def get_provider_by_name(self, name: str) -> List[JobProvider]:
        """
        Get all job providers with the given name.
        :param name: Name of the job provider.
        :return: List of job providers with the given name.
        """
        result = [provider for provider in self._provider.values()
                  if provider.name == name]
        if len(result) == 0:
            raise KeyError(f"Provider {name} not registered!")
        return result

    def get_provider(self, module_id: int) -> JobProvider:
        if type(module_id) is not int:
            module_id = int(module_id)

        if module_id not in self._provider:
            raise KeyError(f"Provider {module_id} not registered!")
        return self._provider[module_id]

    def get_all_provider(self) -> List[JobProvider]:
        return list(self._provider.values())

    def get_config_component(self, module_id: ModuleIdentifier) -> WebComponent:
        if module_id not in self._provider:
            raise ValueError(f"Provider {module_id} not registered")
        return self._provider[module_id].config_component

    def get_client_module_url(self) -> str:
        pass

    def validate_job(self, module_id: ModuleIdentifier, config: dict) -> bool:
        if module_id not in self._provider:
            raise ValueError(f"Provider {module_id} not registered")
        return self._provider[module_id].validate_config(config)

    def create_job(self,
                   module_id: int,
                   config: dict,
                   name: str) -> object:
        from interface.data_objects import JobDO

        if module_id not in self._provider:
            raise ValueError(f"Provider {module_id} not registered")
        if not self.validate_job(module_id, config):
            raise ValueError("Invalid job configuration")

        job_data = self._provider[module_id].create_job(config)

        with self._db.create_session() as session:
            job = JobManager.create(session, job_data, name)
            session.commit()
            return JobDO.from_db(job)

    def delete_jobs(self, ids: list, force: bool = False) -> List[int]:
        """
        Deletes jobs with the given IDs from the database.
        :param ids: List of job IDs to delete.
        :param force: If True, force delete jobs even if they are running.
        """

        deleted_ids = []
        with self._db.create_session() as session:
            for id in ids:
                try:
                    JobManager.delete(session, id, force)
                    deleted_ids.append(id)
                except Exception as e:
                    logging.error(f'Failed to delete job {id}: {str(e)}')
            session.commit()
        return deleted_ids

    def assign_job(self, job_ids: List[int], client_id: int) -> None:
        with self._db.create_session() as session:
            for id in job_ids:
                JobManager(session, id).assign(client_id)
            session.commit()

    def unassign_job(self, job_ids: List[int], force: bool) -> None:
        with self._db.create_session() as session:
            for id in job_ids:
                JobManager(session, id).unassign(force)
            session.commit()

    def get_unassigned_jobs(self) -> List:
        """
        Get all unassigned jobs.
        :return: List of unassigned jobs.
        """
        with self._db.create_session() as session:
            from interface.data_objects import JobDO

            return [JobDO.from_db(j)
                    for j in JobManager.all_unassigned(session)]
