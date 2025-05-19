

import logging
import flask_socketio
from interface.data_objects import ClientDO, ClientProgressDO, JobDO
import model.db_model.models as db_model
import model.local_model.models as local_model

from utils.db.db_context import DBContext
from utils.model_managing.subject_manager import SubjectManager
from utils.session.staging_session import (
    AddDict, DeleteDict, UpdateDict, StagingSession
)


class UpdateEventService:

    class EventStage(StagingSession):
        @staticmethod
        def _emit(event: str, args: dict):
            flask_socketio.emit(event, args,
                                namespace='/update', broadcast=True)
            logging.debug(f'Emitted event {event} with args {args}')

        def __init__(self):
            super().__init__()

        def _flush_staged_data(
                self, deletes: DeleteDict, adds: AddDict, updates: UpdateDict):

            try:
                self._emit('flush', {
                    'deletes': deletes,
                    'adds': adds,
                    'updates': updates
                })
                for type_, objects in adds.items():
                    self._emit(f'{type_}-added',
                               [o.__dict__ for o in objects])

                for type_, ids in deletes.items():
                    self._emit(f'{type_}-deleted', ids)

                for type_, entity_updates in updates.items():
                    self._emit(f'{type_}-changed', [{
                        'id': id,
                        'updates': updates
                    } for id, updates in entity_updates.items()])
            except Exception as e:
                logging.error(f'Failed to emit update event: {e}')

    def __init__(self,
                 db: DBContext, sm: SubjectManager):
        self._sm = sm
        self._db = db

        db_notifier = db.get_notifier()
        db_notifier.set_context_factory(lambda: UpdateEventService.EventStage())

        db_notifier.add_listener(str(db_model.Client),
                                 self.on_client_event)
        db_notifier.add_listener(str(db_model.Job),
                                 self.on_job_event)
        db_notifier.add_listener(str(db_model.JobScheduleEntry),
                                 self.on_schedule_entry_event)

        sm_notifier = sm.get_notifier()
        sm_notifier.set_context_factory(lambda: UpdateEventService.EventStage())
        sm_notifier.add_listener(str(local_model.ClientSession),
                                 self.on_client_session_event)

    def on_client_event(self,
                        context: EventStage,
                        event: str, obj: object, data: dict):
        client: db_model.Client = obj

        if event == 'add':
            context.stage_add('client', ClientDO.create(client, False))
        elif event == 'delete':
            context.stage_delete('client', client.id)
        elif event == 'update':
            context.stage_update(
                'client', client.id, ClientDO.filter_updates(data))

    def on_client_session_event(self,
                                context: EventStage,
                                event: str, obj: object, data: dict):

        client_session: local_model.ClientSession = obj

        if event == 'add':
            context.stage_update('client', client_session.client_id,
                                 {'connected': True})
            context.stage_add('client_progress',
                              ClientProgressDO.create(client_session))

        elif event == 'delete':
            context.stage_update('client', client_session.client_id,
                                 {'connected': False})
            context.stage_delete('client_progress', client_session.client_id)

        elif event == 'update':
            context.stage_update(
                'client_progress',
                client_session.client_id,
                ClientProgressDO.create(client_session).__dict__)

    def on_job_event(self,
                     context: EventStage,
                     event: str, obj: object, data: dict):
        job: db_model.Job = obj

        if event == 'add':
            context.stage_add('job', JobDO.from_db(job))
        elif event == 'delete':
            context.stage_delete('job', job.id)
        elif event == 'update':
            context.stage_update('job', job.id, JobDO.filter_updates(data))

    def on_schedule_entry_event(self,
                                context: EventStage,
                                event: str, obj: object, data: dict):
        entry: db_model.JobScheduleEntry = obj

        logging.debug(f'schedule_entry ({entry}) - {event} - ')

        if event == 'add':
            context.stage_update('job', entry.job_id,
                                 {'client_id': entry.client_id})

        if event == 'delete':
            context.stage_update('job', entry.job_id,
                                 {'client_id': -1})

        if event == 'update':
            context.stage_update('job', entry.job_id,
                                 {'client_id': entry.client_id})
