from __future__ import annotations

import logging
from typing import TYPE_CHECKING, List
from jodiscore.dataobjects.module_identifier import ModuleIdentifier
from jodiscore.dataobjects.web_component import WebComponent
from jodiscore.exceptions.invalid_state_error import InvalidStateError

from jodisutils.db.db_context import DBContext
from model.manager.job_manager import JobManager

if TYPE_CHECKING:
    from model.job import Job
    from model.manager.client_manager import ClientManager


class JobService:
    def __init__(self, db: DBContext):
        self._db = db

    def start_job(self, job_id: int) -> None:
        with self._db.create_session() as session:
            job = JobManager(session, job_id)
            job_model = job.model()
            if job_model.sub_state != Job.SubState.SCHEDULED:
                raise InvalidStateError("Job is not in SCHEDULED state")

            client = ClientManager(session,
                                   job_model.schedule_entry.client_id, True)
            if client.get_active_job() is not None:
                raise InvalidStateError("Client has an active job")

            job_model.sub_state = Job.SubState.RUNNING

            session.commit()

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

        if module_id not in self._provider:
            raise ValueError(f"Provider {module_id} not registered")
        if not self.validate_job(module_id, config):
            raise ValueError("Invalid job configuration")

        job_data = self._provider[module_id].create_job(config)

        with self._db.create_session() as session:
            job = JobManager.create(session, job_data, name)
            session.commit()
            return job.dataobject

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
            return [j.dataobject for j in JobManager.all_unassigned(session)]
