from __future__ import annotations
from typing import TYPE_CHECKING

from model.db_model_base import Base

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey

if TYPE_CHECKING:
    from model.job import Job
    from model.client import Client


class JobScheduleEntry(Base):

    __tablename__ = 'JobScheduleEntry'

    id: Mapped[int] = mapped_column("Id", primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        "JobId", ForeignKey('Job.Id', ondelete='CASCADE'))
    client_id: Mapped[int] = mapped_column(
        "ClientId", ForeignKey('Client.Id', ondelete='CASCADE'))

    rank: Mapped[int] = mapped_column("Rank")

    job: Mapped['Job'] = relationship(back_populates='schedule_entry')
    client: Mapped['Client'] = relationship(back_populates='schedule')

    def __repr__(self) -> str:
        return (
            f"ScheduleEntry(id: {self.id}, "
            f"cid: {self.client_id}[rank: {self.rank}] -> jid: {self.job_id})"
        )
