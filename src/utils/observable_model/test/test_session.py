

import unittest

from src.utils.observable_model.attribute import Attribute
from src.utils.observable_model.subject_session import SubjectSession
from src.utils.observable_model.subject import Subject


class DummySubject(Subject):
    a = Attribute('A', int, primary_key=True)
    b = Attribute('b', str)


class SessionTest(unittest.TestCase):

    def test_change_tracking_and_rollback(self):

        a = DummySubject(a=0, b='a')
        b = DummySubject(a=1, b='b')
        c = DummySubject(a=2, b='c')
        d = DummySubject(a=3, b='d')
        e = DummySubject(a=4, b='e')

        subjects = set([a, b, c, d, e])
        session = SubjectSession(subjects)

        # assert changes are tracked (dirty c)
        c.a = -1
        self.assertSetEqual(session._dirty, {c})
        self.assertDictEqual(session.get_changes(c),
                             {'A': SubjectSession.Change(2, -1)})

        # assert adds are tracked (add f)
        f = DummySubject(a=5, b='f')
        session.add(f)

        self.assertSetEqual(session._new, {f})
        self.assertSetEqual(session._dirty, {c})
        self.assertDictEqual(session.get_changes(c),
                             {'A': SubjectSession.Change(2, -1)})
        self.assertTrue(f in session._subjects)

        # assert deletes are tracked and change history is preserved (delete c)
        session.delete(c)

        self.assertSetEqual(session._new, {f})
        self.assertSetEqual(session._deleted, {c})
        self.assertSetEqual(session._dirty, set())
        self.assertDictEqual(session.get_changes(c),
                             {'A': SubjectSession.Change(2, -1)})

        # assert changes of deleted subjects are not tracked
        c.a = 3
        self.assertSetEqual(session._new, {f})
        self.assertSetEqual(session._deleted, {c})
        self.assertSetEqual(session._dirty, set())
        self.assertDictEqual(session.get_changes(c),
                             {'A': SubjectSession.Change(2, -1)})

        # assert changes of new subjects are tracked but not marked as dirty
        f.b = "test"
        self.assertSetEqual(session._new, {f})
        self.assertSetEqual(session._deleted, {c})
        self.assertSetEqual(session._dirty, set())
        self.assertDictEqual(session.get_changes(f),
                             {'b': SubjectSession.Change('f', 'test')})

        # assert original and current value are tracked
        e.b = "test"
        e.b = "test2"
        self.assertSetEqual(session._new, {f})
        self.assertSetEqual(session._deleted, {c})
        self.assertSetEqual(session._dirty, {e})
        self.assertDictEqual(session.get_changes(e),
                             {'b': SubjectSession.Change('e', 'test2')})

        # assert subject set is updated
        self.assertSetEqual(session._subjects, {a, b, d, e, f})

        # assert dirty flag is restored after deleting and re-adding a subject
        session.delete(e)
        self.assertSetEqual(session._new, {f})
        self.assertSetEqual(session._deleted, {c, e})
        self.assertSetEqual(session._dirty, set())
        self.assertDictEqual(session.get_changes(e),
                             {'b': SubjectSession.Change('e', 'test2')})
        session.add(e)
        self.assertSetEqual(session._new, {f})
        self.assertSetEqual(session._deleted, {c})
        self.assertSetEqual(session._dirty, {e})
        self.assertDictEqual(session.get_changes(e),
                             {'b': SubjectSession.Change('e', 'test2')})

        # assert rollback resets original state
        session.rollback()

        self.assertSetEqual(session._new, set())
        self.assertSetEqual(session._dirty, set())
        self.assertSetEqual(session._deleted, set())
        self.assertDictEqual(session._changes, {})

        self.assertSetEqual(session._subjects, {a, b, c, d, e})
        self.assertListEqual([a.a, b.a, c.a, d.a, e.a, f.a],
                             [0, 1, 2, 3, 4, 5])
        self.assertListEqual([a.b, b.b, c.b, d.b, e.b, f.b],
                             ['a', 'b', 'c', 'd', 'e', 'f'])

    def test_commit(self):
        a = DummySubject(a=0, b='a')
        b = DummySubject(a=1, b='b')
        c = DummySubject(a=2, b='c')
        d = DummySubject(a=3, b='d')
        e = DummySubject(a=4, b='e')
        f = DummySubject(a=5, b='f')

        subjects = set([a, b, c, d, e])

        commit_flushed = False

        def on_commit(session: SubjectSession, new, dirty, deleted):
            nonlocal commit_flushed
            commit_flushed = True
            self.assertSetEqual(new, {f})
            self.assertSetEqual(dirty, {a})
            self.assertSetEqual(deleted, {b})
            self.assertEqual(session.get_changes(a),
                             {'A': SubjectSession.Change(0, -1)})

        # assert context manager without commit rolls back changes
        with SubjectSession(subjects) as session:
            session.on_commit = on_commit
            a.a = -1
            session.delete(b)
            session.add(f)

        self.assertEqual(a.a, 0)
        self.assertTrue(b in subjects)
        self.assertFalse(f in subjects)
        self.assertFalse(commit_flushed)

        # assert context manager with commit flushes changes
        with SubjectSession(subjects) as session:
            session.on_commit = on_commit
            a.a = -1
            session.delete(b)
            session.add(f)
            session.commit()

        self.assertEqual(a.a, -1)
        self.assertFalse(b in subjects)
        self.assertTrue(f in subjects)
        self.assertTrue(commit_flushed)

    def test_get(self):
        a = DummySubject(a=0, b='a')
        b = DummySubject(a=1, b='b')
        c = DummySubject(a=2, b='c')
        d = DummySubject(a=3, b='d')
        e = DummySubject(a=4, b='e')

        subjects = set([a, b, c, d, e])
        session = SubjectSession(subjects)

        self.assertIsNone(session.get(int, 1, False))
        with self.assertRaises(IndexError):
            session.get(int, 1, True)

        self.assertEqual(session.get(DummySubject, 1, False), b)

        self.assertIsNone(session.get(DummySubject, 5, False))
        with self.assertRaises(IndexError):
            session.get(int, 5, True)
