from dataclasses import dataclass
import logging
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import Session

from aithena.utils.config_utils import assert_fields_in_dict

from utils.observable_model.change_notifier import ChangeNotifier


class DBContext:

    @dataclass
    class Config:
        sql_user: str
        sql_pw: str
        sql_server: str
        sql_db: str

        @staticmethod
        def from_dict(cfg: dict):
            assert_fields_in_dict(cfg, ['user', 'password', 'host', 'db'])
            return DBContext.Config(cfg['user'], cfg['password'],
                                    cfg['host'], cfg['db'])

        @staticmethod
        def get_test_config():
            return DBContext.Config("", "", "", "")

    def __init__(self, cfg: Config):
        if len(cfg.sql_user) == 0:
            credentials = '/'
        else:
            credentials = f"{cfg.sql_user}:{cfg.sql_pw}@"

        if len(cfg.sql_server) == 0:
            target = ':memory:'
        else:
            target = f"{cfg.sql_server}/{cfg.sql_db}"

        connect_query = f'mysql+pymysql://{credentials}{target}'
        self._engine = create_engine(connect_query)
        logging.info('db engine created')

        self._notifier = ChangeNotifier()

    def get_notifier(self) -> ChangeNotifier:
        return self._notifier

    def create_session(self) -> Session:
        logging.debug('created db session')
        session = Session(self._engine)

        def after_flush(session: Session, context):

            deleted = session.deleted
            new = session.new.difference(deleted)
            dirty = session.dirty.difference(deleted)

            with self._notifier.begin_session() as notifier:
                for obj in deleted:
                    notifier.notify_delete(obj)

                for obj in new:
                    notifier.notify_add(obj)

                for obj in dirty:
                    changed_attributes \
                        = [a for a in inspect(obj).attrs
                           if a.history.has_changes()]
                    changes = {a.key: a.history.added[0]
                               for a in changed_attributes}
                    notifier.notify_update(obj, changes)

        event.listen(session, 'after_flush', after_flush)

        return session
