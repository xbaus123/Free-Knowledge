import unittest

from solution import greet


class GreetTest(unittest.TestCase):
    def test_greets_by_name(self):
        """greets someone by name"""
        self.assertEqual(greet("Ada"), "Hello, Ada!")

    def test_empty_name(self):
        """falls back to 'world' for an empty name"""
        self.assertEqual(greet(""), "Hello, world!")
