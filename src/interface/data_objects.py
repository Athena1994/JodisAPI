

from dataclasses import dataclass
import enum

from model.db_model import models


@dataclass
class ClientDO:
    id: int
    name: str
    connected: bool
    state: str

    @staticmethod
    def create(client: models.Client, is_connected: bool):
        return ClientDO(client.id,
                        client.name,
                        is_connected,
                        client.state.value)

    @staticmethod
    def filter_updates(updates: dict):
        updates = {k: updates[k] for k in updates
                   if k in ['name', 'state']}
        return updates


@dataclass
class JobSessionDO:
    id: int
    job_id: int
    epoch_ids: list[int]
    max_epoch: int
    snapshot: str

    @staticmethod
    def from_db(session: models.JobSession):
        return JobSessionDO(id=session.id,
                            job_id=session.job_id,
                            epoch_ids=[e.id for e in session.epochs],
                            max_epoch=session.max_epoch,
                            snapshot=session.snapshot)


@dataclass
class JobDO:
    id: int
    state: str
    sub_state: str
    client_id: int
    rank: int
    config: dict
    name: str
    description: str

    @staticmethod
    def from_db(job: models.Job):
        client_id = (
            job.schedule_entry.client_id
            if job.schedule_entry is not None else -1
        )
        rank = job.schedule_entry.rank if job.schedule_entry is not None else -1

        return JobDO(id=job.id,
                     state=job.state.value,
                     sub_state=job.sub_state.value,
                     client_id=client_id,
                     rank=rank,
                     config=job.configuration,
                     name=job.name,
                     description=job.description)

    @staticmethod
    def filter_updates(updates: dict):
        updates = {k: updates[k] for k in updates
                   if k in ['state', 'sub_state', 'client_id', 'rank', 'config',
                            'name', 'description']}

        updates.update({k: v.value
                        for k, v in updates.items()
                        if isinstance(v, enum.Enum)})

        return updates
