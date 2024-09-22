import enum
from typing import List, Optional
from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from datetime import datetime


class Base(DeclarativeBase):
    pass


# --- job --------------------------

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

    configuration: Mapped[JSON] = mapped_column('Configuration', type_=JSON)
    creation_timestamp: Mapped[datetime] = mapped_column(
        'CreationTimestamp', default=func.current_timestamp())
    name: Mapped[str] = mapped_column("Name", String(64), nullable=True)
    description: Mapped[str] = mapped_column(
        "Description", String(256), nullable=True)
    state: Mapped[State] = mapped_column(
        'State', default=State.UNASSIGNED)
    sub_state: Mapped[SubState] = mapped_column(
        'SubState', default=SubState.CREATED)

    schedule_entry: Mapped["JobScheduleEntry"] = relationship(
        back_populates='job', cascade='all, delete-orphan', uselist=False)

    session: Mapped[Optional["JobSession"]] \
        = relationship(back_populates='job')

    def __repr__(self) -> str:
        return f"Job({self.id}, {self.name}, {self.state}, {self.SubState})"


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

    def __repr__(self) -> str:
        return (
            f"ScheduleEntry(id: {self.id}, "
            f"cid: {self.client_id}[rank: {self.rank}] -> jid: {self.job_id})"
        )


# --- client --------------------------

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

    def __repr__(self) -> str:
        return f"Client (id: {self.id}, {self.name})"


# --- session --------------------------

class JobSession(Base):
    __tablename__ = 'Session'

    id: Mapped[int] = mapped_column("Id", primary_key=True, autoincrement=True)
    job_id: Mapped[int] = mapped_column(
        'JobId', ForeignKey('Job.Id', ondelete='CASCADE'))

    max_epoch: Mapped[int] = mapped_column('MaxEpoch', nullable=True)
    snapshot: Mapped[str] = mapped_column('Snapshot', String(256))

    epochs: Mapped[List["Epoch"]] = relationship(
        'Epoch', back_populates='session', cascade='all, delete-orphan')
    job: Mapped[Job] = relationship(back_populates='session')


class Epoch(Base):
    __tablename__ = 'Epoch'

    id: Mapped[int] = mapped_column(
        "Id", primary_key=True, autoincrement=True)

    session_id: Mapped[int] = mapped_column(
        'SessionId', ForeignKey('Session.Id', ondelete='CASCADE'))

    start_timestamp: Mapped[datetime] = mapped_column('StartTimestamp')
    end_timestamp: Mapped[datetime] = mapped_column('EndTimestamp')
    result: Mapped[JSON] = mapped_column('Result', type_=JSON)

    session: Mapped[JobSession] = relationship(back_populates='epochs')
