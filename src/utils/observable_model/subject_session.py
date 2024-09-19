

from dataclasses import dataclass
from src.utils.observable_model.subject import Subject


class SubjectSession:

    @dataclass
    class Change:
        old: object
        new: object

    def __init__(self, subjects: set[Subject]):
        self._subjects = subjects

        for s in self._subjects:
            self.attach(s)

        self._new: set[Subject] = set()
        self._dirty: set[Subject] = set()
        self._deleted: set[Subject] = set()

        self._changes: dict[Subject, dict[str, SubjectSession.Change]] = dict()

    def get_changes(self, subject: Subject):
        return self._changes.get(subject, {})

    def get(self, type_: type, key: object, raise_: bool) -> Subject:
        for s in self._subjects:
            if isinstance(s, type_) and s.get_primary_key() == key:
                return s

        if raise_:
            raise IndexError('Subject not found')

        return None

    def attach(self, subject: Subject):
        subject.on_attribute_changed = (
            lambda name, old_value, new_value:
                self.on_subject_attribute_changed(
                    subject,
                    name,
                    old_value,
                    new_value)
        )

    def detach(self, subject: Subject):
        subject.on_attribute_changed = None

    def add(self, subject: Subject):
        if subject in self._subjects:
            raise ValueError('Subject already in session')
        self._subjects.add(subject)

        if subject in self._deleted:
            self._deleted.remove(subject)
            if subject in self._changes:
                self._dirty.add(subject)
        else:
            self._new.add(subject)

        self.attach(subject)

    def delete(self, subject: Subject):
        if subject not in self._subjects:
            raise ValueError('Subject not in session')
        self._subjects.remove(subject)

        if subject in self._new:
            self._new.remove(subject)

        if subject in self._dirty:
            self._dirty.remove(subject)

        self._deleted.add(subject)

        self.detach(subject)

    def on_subject_attribute_changed(self,
                                     target: Subject,
                                     name: str,
                                     old_value: object,
                                     new_value: object):

        if target not in self._dirty and target not in self._new:
            self._dirty.add(target)

        if target not in self._changes:
            self._changes[target] = {}

        change_dict = self._changes[target]

        if name in change_dict:
            change_dict[name].new = new_value
        else:
            change_dict[name] = SubjectSession.Change(old_value, new_value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _clear(self):
        self._new.clear()
        self._dirty.clear()
        self._deleted.clear()
        self._changes.clear()

    def on_commit(self,
                  session: 'SubjectSession',
                  new: set[Subject],
                  dirty: set[Subject],
                  deleted: set[Subject]):
        pass

    def commit(self):
        self.on_commit(self, self._new, self._dirty, self._deleted)
        self._clear()

    def rollback(self):
        for subject, changes in self._changes.items():
            for att, change in changes.items():
                subject.__dict__[att] = change.old

        for subject in self._new:
            self.detach(subject)
            self._subjects.remove(subject)

        for subject in self._deleted:
            self.attach(subject)
            self._subjects.add(subject)

        self._clear()

    def close(self):
        self.rollback()
        for s in self._subjects:
            self.detach(s)
