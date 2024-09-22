
import unittest

from src.utils.model_managing.attribute import Attribute
from src.utils.model_managing.subject import Subject


class SubjectTest(unittest.TestCase):
    class MockSubject(Subject):
        a = Attribute('a', int, primary_key=True)
        b = Attribute('b', str, 'test')

        def __init__(self, **kwargs):
            super().__init__(**kwargs)
            self.changes = []

            def callback(name, old_value, new_value):
                self.changes.append((name, old_value, new_value))

            self.on_attribute_changed = callback

    def test_subject_init(self):

        class InvalidSubject(Subject):
            a = Attribute('a', int, 0)
            b = Attribute('b', str, 'test')
        with self.assertRaises(ValueError):
            _ = InvalidSubject()

        with self.assertRaises(ValueError):
            _ = self.MockSubject()

        s = self.MockSubject(a=1)

        self.assertEqual(s.a, 1)
        self.assertEqual(s.b, 'test')

        self.assertListEqual(s.changes, [])

        s.a = 2
        self.assertListEqual(s.changes, [('a', 1, 2)])

        s.b = 'new'
        self.assertListEqual(s.changes, [('a', 1, 2), ('b', 'test', 'new')])
