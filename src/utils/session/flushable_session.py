

class FlushableSession:

    def __init__(self, commit_on_exit: bool):
        self._commit_on_exit = commit_on_exit
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._closed:
            return

        self.close(commit=self._commit_on_exit and exc_type is None)

    def _flush(self):
        pass

    def _rollback(self):
        pass

    def _commit(self):
        self.flush()

    def _clear(self):
        pass

    def _close(self, commit: bool):
        if commit:
            self.commit()
        else:
            self.rollback()

    def close(self, commit: bool):
        self.before_close(self)
        self._close(commit)
        self._closed = True
        self.after_close(self)

    def clear(self):
        self.before_clear(self)
        self._clear()
        self.after_clear(self)

    def commit(self):
        if self._closed:
            raise Exception('Session is closed')
        self.before_commit(self)
        self._commit()
        self.after_commit(self)

    def flush(self):
        if self._closed:
            raise Exception('Session is closed')
        self.before_flush(self)
        self._flush()
        self.clear()
        self.after_flush(self)

    def rollback(self):
        if self._closed:
            raise Exception('Session is closed')
        self.before_rollback(self)
        self._rollback()
        self.clear()
        self.after_rollback(self)

    def before_commit(self, session: 'FlushableSession'):
        pass

    def before_rollback(self, session: 'FlushableSession'):
        pass

    def before_close(self, session: 'FlushableSession'):
        pass

    def before_flush(self, session: 'FlushableSession'):
        pass

    def before_clear(self, session: 'FlushableSession'):
        pass

    def after_clear(self, session: 'FlushableSession'):
        pass

    def after_commit(self, session: 'FlushableSession'):
        pass

    def after_rollback(self, session: 'FlushableSession'):
        pass

    def after_flush(self, session: 'FlushableSession'):
        pass

    def after_close(self, session: 'FlushableSession'):
        pass
