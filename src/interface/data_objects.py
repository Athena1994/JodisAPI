

from dataclasses import dataclass
import enum

import model.db_model.models as db_model
import model.local_model.models as local_model


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
    state: str
    sub_state: str
    client_id: int
    rank: int
    config: dict
    name: str
    description: str

    @staticmethod
    def from_db(job: db_model.Job):
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


# @dataclass
# class ModuleVersionDO:
#     version: str
#     api_version: str
#     is_job_processor: bool
#     error: bool

#     @staticmethod
#     def from_model(version: local_model.ServerModuleVersion):
#         return ModuleVersionDO(version.version,
#                                version.api_version,
#                                version.is_job_processor,
#                                version.error is not None)


# @dataclass
# class ModuleDO:
#     name: str
#     description: str
#     enabled: bool
#     autostart: bool
#     running: bool
#     has_error: bool
#     error: str
#     versions: list[ModuleVersionDO]
#     version: str
#     job_processor: bool

#     @staticmethod
#     def from_model(module: local_model.ServerModule,
#                    versions: List[local_model.ServerModuleVersion],
#                    active_version: local_model.ServerModuleVersion):

#         running: bool \
#             = active_version is not None and active_version.running
#         job_processor: bool \
#             = active_version is not None and active_version.is_job_processor
#         has_error: bool \
#             = (module.error is not None) or (
#                 (active_version is not None) and active_version.error)
#         error: str = ''
#         if module.error is not None:
#             error = module.error.description
#         elif active_version is not None and active_version.error is not None:
#             error = active_version.error.description

#         name: str = module.name
#         description: str = module.description
#         enabled: bool = module.enabled
#         autostart: bool = module.autostart
#         version: str = module.active_version

#         versions = [ModuleVersionDO.from_model(v) for v in versions]

#         return ModuleDO(name,
#                         description,
#                         enabled,
#                         autostart,
#                         running, has_error, error,
#                         versions,
#                         version, job_processor)
