import unittest

from solution import cpu_time, function_at, hottest, profile

SYMBOLS = [(0x1000, "main"), (0x1400, "parse"), (0x2000, "draw")]


class FunctionAt(unittest.TestCase):
    def test_inside(self):
        """Addresses inside each function"""
        self.assertEqual(function_at(SYMBOLS, 0x1004), "main")
        self.assertEqual(function_at(SYMBOLS, 0x1500), "parse")
        self.assertEqual(function_at(SYMBOLS, 0x2fff), "draw")

    def test_boundaries(self):
        """A function starts exactly at its start address"""
        self.assertEqual(function_at(SYMBOLS, 0x1000), "main")
        self.assertEqual(function_at(SYMBOLS, 0x13ff), "main")
        self.assertEqual(function_at(SYMBOLS, 0x1400), "parse")
        self.assertEqual(function_at(SYMBOLS, 0x2000), "draw")

    def test_last_runs_forever(self):
        """The last function has no end"""
        self.assertEqual(function_at(SYMBOLS, 0xFFFFFF), "draw")

    def test_below_first(self):
        """Below the first function: no function"""
        self.assertIsNone(function_at(SYMBOLS, 0x0FFF))
        self.assertIsNone(function_at(SYMBOLS, 0))

    def test_empty_table(self):
        """No symbols, no function"""
        self.assertIsNone(function_at([], 0x1234))


class Profile(unittest.TestCase):
    SAMPLES = [0x1004, 0x1500, 0x1510, 0x2100, 0x1520, 0x0500]

    def test_counts(self):
        """Each sample counts toward its function"""
        self.assertEqual(profile(self.SAMPLES, SYMBOLS), {"main": 1, "parse": 3, "draw": 1, "?": 1})

    def test_no_samples(self):
        """No samples, no counts"""
        self.assertEqual(profile([], SYMBOLS), {})

    def test_hottest(self):
        """The example from the lesson"""
        self.assertEqual(hottest(self.SAMPLES, SYMBOLS, 2), [("parse", 50.0), ("?", 16.7)])

    def test_hottest_ties_by_name(self):
        """Ties are broken alphabetically"""
        samples = [0x2000, 0x1000, 0x1400, 0x2001]
        self.assertEqual(hottest(samples, SYMBOLS, 3), [("draw", 50.0), ("main", 25.0), ("parse", 25.0)])

    def test_hottest_more_than_exist(self):
        """Asking for more functions than were sampled gives them all"""
        self.assertEqual(hottest([0x1000, 0x1001, 0x1002], SYMBOLS, 10), [("main", 100.0)])

    def test_rounding(self):
        """Percentages are rounded to one decimal place"""
        samples = [0x1000, 0x1400, 0x1401]
        self.assertEqual(hottest(samples, SYMBOLS, 2), [("parse", 66.7), ("main", 33.3)])


class CpuTime(unittest.TestCase):
    EVENTS = [
        (0, "on", "java", 101), (40, "off", "java", 101),
        (40, "on", "Xorg", 0), (55, "off", "Xorg", 0),
        (55, "on", "java", 101), (60, "off", "java", 101),
    ]

    def test_totals(self):
        """Time on the CPU adds up per program"""
        self.assertEqual(cpu_time(self.EVENTS), {"java": 45, "Xorg": 15})

    def test_filter_by_user(self):
        """Like the uid == 101 predicate"""
        self.assertEqual(cpu_time(self.EVENTS, uid=101), {"java": 45})
        self.assertEqual(cpu_time(self.EVENTS, uid=0), {"Xorg": 15})
        self.assertEqual(cpu_time(self.EVENTS, uid=7), {})

    def test_unmatched_off(self):
        """An off with no on is ignored"""
        events = [(5, "off", "a", 1), (10, "on", "a", 1), (12, "off", "a", 1), (20, "off", "a", 1)]
        self.assertEqual(cpu_time(events), {"a": 2})

    def test_still_running(self):
        """A program still on the CPU at the end isn't counted yet"""
        events = [(0, "on", "a", 1), (3, "off", "a", 1), (3, "on", "b", 1)]
        self.assertEqual(cpu_time(events), {"a": 3})

    def test_multicore_overlap(self):
        """Two programs can be on CPUs at the same time"""
        events = [(0, "on", "a", 1), (1, "on", "b", 1), (4, "off", "a", 1), (9, "off", "b", 1)]
        self.assertEqual(cpu_time(events), {"a": 4, "b": 8})

    def test_empty(self):
        """No events"""
        self.assertEqual(cpu_time([]), {})


if __name__ == "__main__":
    unittest.main()
