
from datetime import datetime
import enum

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from jodiscore.dataobjects.job import JobDO
from jodiscore.server.job_provider.job_provider_control \
    import JobProviderControl

from jodisutils.injector import inject

from model.db_model_base import Base
from model.job_schedule_entry import JobScheduleEntry
from model.job_data import JobData


class Job(Base):
    __tablename__ = 'Job'

    class SubState(enum.Enum):
        CREATED = 'CREATED'
        RETURNED = 'RETURNED'

        SCHEDULED = 'SCHEDULED'
        RUNNING = 'RUNNING'

        FAILED = 'FAILED'
        FINISHED = 'FINISHED'
        ABORTED = 'ABORTED'

    class State(enum.Enum):
        UNASSIGNED = 'UNASSIGNED'
        ASSIGNED = 'ASSIGNED'
        FINISHED = 'FINISHED'

    id: Mapped[int] = mapped_column("Id", primary_key=True, autoincrement=True)

    data: Mapped[JobData] = mapped_column(
        "JobData",
        type_=JobData.Type)

    name: Mapped[str] = mapped_column("Name", String(64), nullable=True)

    creation_timestamp: Mapped[datetime] = mapped_column(
        'CreationTimestamp', default=func.current_timestamp())
    state: Mapped[State] = mapped_column(
        'State', default=State.UNASSIGNED)
    sub_state: Mapped[SubState] = mapped_column(
        'SubState', default=SubState.CREATED)

    schedule_entry: Mapped[JobScheduleEntry] = relationship(
        back_populates='job', cascade='all, delete-orphan', uselist=False)

    def __repr__(self) -> str:
        return f"Job({self.id}, {self.name}, {self.state}, {self.SubState})"

    @property
    @inject
    def dataobject(self, jpc: JobProviderControl) -> JobDO:

        if self.schedule_entry is not None:
            client_id = self.schedule_entry.client_id
            rank = self.schedule_entry.rank
        else:
            client_id = -1
            rank = -1

        return JobDO(id=self.id,
                     client_id=client_id,

                     module_id=self.data.module_id,
                     module_name=jpc.get_provider(self.data.module_id).name,

                     state=self.state.value,
                     sub_state=self.sub_state.value,

                     rank=rank,

                     config=self.data.cfg,
                     name=self.name,
                     payload=self.data.payload_key,

                     timestamp=str(self.creation_timestamp))
