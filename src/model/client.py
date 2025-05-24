
import enum
from typing import List
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from jodiscore.dataobjects.client import ClientDO
from jodisutils.architecture.injector import inject
from model.db_model_base import Base
from model.job_schedule_entry import JobScheduleEntry
from services.client_connection_service import ClientConnectionService


class Client(Base):
    __tablename__ = 'Client'

    class State(enum.Enum):
        ACTIVE = 'ACTIVE'
        SUSPENDED = 'SUSPENDED'

    id: Mapped[int] = mapped_column("Id", primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column("Name", String(64), nullable=True)
    schedule: Mapped[List[JobScheduleEntry]] = relationship(
        back_populates='client', cascade='all, delete-orphan',
        order_by=JobScheduleEntry.rank)
    state: Mapped[State] = mapped_column(
        "State", nullable=False, default=State.SUSPENDED)

    def __repr__(self) -> str:
        return f"Client (id: {self.id}, {self.name})"

    @property
    @inject
    def dataobject(self, ccs: ClientConnectionService) -> ClientDO:

        return ClientDO(self.id,
                        self.name,
                        ccs.is_connected(self.id),
                        self.state.value)
