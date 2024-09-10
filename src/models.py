import enum
from typing import List
from sqlalchemy import JSON, ForeignKey, String, event
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from datetime import datetime


class Base(DeclarativeBase):
    pass


class Job(Base):
    __tablename__ = 'Job'

    id: Mapped[int] = mapped_column("Id", primary_key=True, autoincrement=True)

    configuration: Mapped[JSON] = mapped_column('Configuration', type_=JSON)
    creation_timestamp: Mapped[datetime] = mapped_column(
        'CreationTimestamp', default=func.current_timestamp())
    name: Mapped[str] = mapped_column("Name", String(64), nullable=True)
    description: Mapped[str] = mapped_column(
        "Description", String(256), nullable=True)

    states: Mapped[List["JobStatus"]] = relationship(
        back_populates='job', cascade='all, delete-orphan',)

    schedule_entry: Mapped["JobScheduleEntry"] = relationship(
        back_populates='job', cascade='all, delete-orphan', uselist=False)


class JobStatus(Base):
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

    __tablename__ = 'JobStatus'

    id: Mapped[int] = mapped_column("Id", primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        "JobId", ForeignKey('Job.Id', ondelete='CASCADE'))

    state: Mapped[State] = mapped_column("State")
    sub_state: Mapped[SubState] = mapped_column("SubState")
    creation_timestamp: Mapped[datetime] = mapped_column(
        'Timestamp', default=func.current_timestamp())

    job: Mapped["Job"] = relationship(back_populates='states')


class JobScheduleEntry(Base):
    __tablename__ = 'JobScheduleEntry'

    id: Mapped[int] = mapped_column("Id", primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        "JobId", ForeignKey('Job.Id', ondelete='CASCADE'))
    client_id: Mapped[int] = mapped_column(
        "ClientId", ForeignKey('Client.Id', ondelete='CASCADE'))

    rank: Mapped[int] = mapped_column("Rank")

    job: Mapped["Job"] = relationship(back_populates='schedule_entry')
    client: Mapped["Client"] = relationship(back_populates='schedule')


class Client(Base):
    __tablename__ = 'Client'

    class State(enum.Enum):
        ACTIVE = 'ACTIVE'
        SUSPENDED = 'SUSPENDED'

    id: Mapped[int] = mapped_column("Id", primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column("Name", String(64), nullable=True)
    schedule: Mapped[List["JobScheduleEntry"]] = relationship(
        back_populates='client', cascade='all, delete-orphan',
        order_by=JobScheduleEntry.rank)
    state: Mapped[State] = mapped_column(
        "State", nullable=False, default=State.SUSPENDED)


def create_initial_job_status(mapper,
                              connection,
                              target: Job):
    status = JobStatus(state=JobStatus.State.UNASSIGNED,
                       sub_state=JobStatus.SubState.CREATED)
    target.states.append(status)


event.listen(Job, 'after_insert', create_initial_job_status)
