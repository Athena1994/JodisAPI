

import unittest

from src.utils.observable_model.attribute import Attribute


old = None
new = None
name = None


class AttributeTest(unittest.TestCase):
    def test_attribute(self):

        class DummyClass:
            a = Attribute('a', int)
            b = Attribute('B', str)

            def on_attribute_changed(self, name_, old_value, new_value):
                global old, new, name
                old = old_value
                new = new_value
                name = name_

        d = DummyClass()

        with self.assertRaises(AttributeError):
            _ = d.a

        with self.assertRaises(ValueError):
            d.a = 'test'

        d.a = 2

        self.assertEqual(old, None)
        self.assertEqual(new, None)
        self.assertEqual(name, None)

        d.a = 1

        self.assertEqual(old, 2)
        self.assertEqual(new, 1)
        self.assertEqual(name, 'a')

        d.b = 'test'
        self.assertEqual(old, 2)
        self.assertEqual(new, 1)
        self.assertEqual(name, 'a')

        d.b = 'test2'
        self.assertEqual(old, 'test')
        self.assertEqual(new, 'test2')
        self.assertEqual(name, 'B')
