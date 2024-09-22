

from utils.notifier.change_notifier import ChangeNotifier
from utils.model_managing.subject_session import SubjectSession
from utils.model_managing.subject import Subject


class SubjectManager:
    def __init__(self):
        self._notifier = ChangeNotifier()
        self._subjects: set[Subject] = set()

        self._active_session = False

    def get_notifier(self):
        return self._notifier

    def on_commit(self, session: SubjectSession,
                  new: set[Subject],
                  dirty: set[Subject],
                  deleted: set[Subject]):
        self._active_session = False

        with self._notifier.create_session() as notifier:
            for s in new:
                notifier.notify_add(s)
            for s in dirty:
                changes = {k: v.new for k, v in session.get_changes(s).items()}
                notifier.notify_update(s, changes)
            for s in deleted:
                notifier.notify_delete(s)

    def create_session(self) -> SubjectSession:
        if self._active_session:
            raise ValueError('there is already an active session')
        self._active_session = True
        session = SubjectSession(self._subjects)
        session.before_commit = self.on_commit
        return session
