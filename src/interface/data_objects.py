

from dataclasses import dataclass
import enum
import json

import model.db_model.models as db_model
import model.local_model.models as local_model
from services.jobs.job_provider import JobProvider
from services.jobs.job_service import JobService
from services.server_modules.utils.web_component import WebComponent
from jodisutils.injector import inject


@dataclass
class ClientDO:
    id: int
    name: str
    connected: bool
    state: str

    @staticmethod
    def create(client: db_model.Client, is_connected: bool):
        return ClientDO(client.id,
                        client.name,
                        is_connected,
                        client.state.value)

    @staticmethod
    def filter_updates(updates: dict):
        updates = {k: updates[k] for k in updates
                   if k in ['name', 'state', 'connected']}
        return updates


@dataclass
class ClientProgressDO:
    client_id: int
    phase: str
    message: str
    percentage_done: float
    estimated_phase_time: float
    estimated_epoch_time: float
    estimated_total_time: float

    @staticmethod
    def create(client_session: local_model.ClientSession):
        prog = ClientProgressDO.calc_progress(client_session)

        return ClientProgressDO(
            client_id=client_session.client_id,
            phase=client_session.phase.value,
            message=client_session.message,
            percentage_done=prog['percentage'],
            estimated_phase_time=prog['estimated_phase_time'],
            estimated_epoch_time=-1,
            estimated_total_time=-1)

    @staticmethod
    def calc_progress(cs: local_model.ClientSession):
        if cs.phase_count == -1:
            return {'percentage': -1, 'estimated_phase_time': -1}

        percentage = cs.phase_ix / cs.phase_count
        estimated_phase_time = (cs.phase_count - cs.phase_ix) * cs.time_per_ix
        return {'percentage': percentage,
                'estimated_phase_time': estimated_phase_time}


@dataclass
class JobSessionDO:
    id: int
    job_id: int
    max_epoch: int
    snapshot: str

    @staticmethod
    def from_db(session: db_model.JobSession):
        return JobSessionDO(id=session.id,
                            job_id=session.job_id,
                            epoch_ids=[e.id for e in session.epochs],
                            max_epoch=session.max_epoch,
                            snapshot=session.snapshot)


@dataclass
class JobDO:
    id: int
    client_id: int

    module_id: str
    module_name: str

    rank: int

    state: str
    sub_state: str

    name: str
    config: dict
    payload: str

    timestamp: str

    @staticmethod
    @inject
    def from_db(job: db_model.Job, js: JobService):

        if job.schedule_entry is not None:
            client_id = job.schedule_entry.client_id
            rank = job.schedule_entry.rank
        else:
            client_id = -1
            rank = -1

        return JobDO(id=job.id,
                     client_id=client_id,

                     module_id=job.data.module_id,
                     module_name=js.get_provider(job.data.module_id).name,

                     state=job.state.value,
                     sub_state=job.sub_state.value,

                     rank=rank,

                     config=job.data.cfg,
                     name=job.name,
                     payload=job.data.payload_key,

                     timestamp=str(job.creation_timestamp))

    @staticmethod
    def filter_updates(updates: dict):
        updates = {k: updates[k] for k in updates
                   if k in ['state', 'sub_state', 'client_id', 'rank', 'config',
                            'name', 'description']}

        updates.update({k: v.value
                        for k, v in updates.items()
                        if isinstance(v, enum.Enum)})

        return updates


@dataclass
class WebComponentDO(dict):
    url: str
    component: str

    @staticmethod
    def create(component: WebComponent):
        return WebComponentDO(
            url=str(component.module_url),
            component=component.component_class
        )


@dataclass
class JobProviderDO(dict):
    id: str
    name: str
    version: str
    hash: str

    client_url: str
    config_component: WebComponentDO

    def to_json(self):
        return json.dumps(self.__dict__)

    @staticmethod
    def create(jp: JobProvider):
        return JobProviderDO(
            str(jp.id),
            name=jp.name,
            version=jp.version,
            hash=jp.src_hash,
            client_url=jp.client_url,
            config_component=WebComponentDO.create(jp.config_component)
        )
