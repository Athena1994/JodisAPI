
from db_model import models
from interface.data_objects import ClientDO, JobDO
from interface.socket.connection import Connection
from interface.socket.connection_manager import ConnectionManager
from interface.socket.update_events.emission_session import EmissionSession
from utils.db.change_notifier import ChangeEmitter
from utils.db.db_context import DBContext


class UpdateEmitter(ChangeEmitter):

    def __init__(self, db: DBContext, cm: ConnectionManager):
        self._cm = cm
        self._db = db

        db_notifier = db.get_notifier()

        db_notifier.add_listener(str(models.Client),
                                 self.on_client_event)
        db_notifier.add_listener(str(models.Job),
                                 self.on_job_event)
        db_notifier.add_listener(str(models.JobScheduleEntry),
                                 self.on_schedule_entry_event)
        db_notifier.set_emitter(self)

        cm_notifier = cm.get_notifier()
        cm_notifier.add_listener(str(Connection),
                                 self.on_connection_event)
        cm_notifier.set_emitter(self)

    def start_session(self, listeners) -> EmissionSession:
        return EmissionSession(listeners)

    def on_client_event(self,
                        session: EmissionSession,
                        event: str, obj: object, data: dict):
        client: models.Client = obj

        if event == 'add':
            session.stage_add(
                'client',
                ClientDO.create(client, self._cm.is_connected(client.id))
            )
        elif event == 'delete':
            session.stage_delete('client', client.id)
        elif event == 'update':
            session.stage_update(
                'client', client.id,
                ClientDO.filter_updates(data)
            )

    def on_connection_event(self,
                            session: EmissionSession,
                            event: str, obj: object, data: dict):
        connection: Connection = obj

        if event == 'add':
            session.stage_update('client', connection.client_id(),
                                 {'connected': True})
        elif event == 'delete':
            session.stage_update('client', connection.client_id(),
                                 {'connected': False})

    def on_job_event(self,
                     session: EmissionSession,
                     event: str, obj: object, data: dict):
        job: models.Job = obj

        if event == 'add':
            session.stage_add(
                'job',
                JobDO.from_db(job)
            )
        elif event == 'delete':
            session.stage_delete('job', job.id)
        elif event == 'update':
            session.stage_update(
                'job', job.id,
                JobDO.filter_updates(data)
            )

    def on_schedule_entry_event(self,
                                session: EmissionSession,
                                event: str, obj: object, data: dict):
        entry: models.JobScheduleEntry = obj

        if event == 'add':
            session.stage_update('job', entry.job_id,
                                 {'client_id': entry.client_id})

        if event == 'delete':
            session.stage_update('job', entry.job_id,
                                 {'client_id': -1})

        if event == 'update':
            session.stage_update('job', entry.job_id,
                                 {'client_id': entry.client_id})
