import time
import unittest

from booking import book_serializable, book_unsafe, book_with_lock
from race import run_concurrently
from shop import open_facility

SIX_PM, SEVEN_PM, EIGHT_PM = 18 * 60, 19 * 60, 20 * 60


def bookings(db, bay=None):
    return [b for b in db.rows("bookings") if bay is None or b["bay_id"] == bay]


def statements(db, isolation=None):
    return [sql for _, iso, sql in db.log if isolation is None or iso == isolation]


class Reproduce(unittest.TestCase):
    def test_unsafe_flow_double_books(self):
        """reproduces the bug: two concurrent bookings of bay 3 at 6 pm both succeed"""
        db = open_facility()
        results = run_concurrently(db, [
            lambda: book_unsafe(db, 3, SIX_PM, SEVEN_PM, "Ada"),
            lambda: book_unsafe(db, 3, SIX_PM, SEVEN_PM, "Grace"),
        ])
        self.assertEqual(results, [True, True])
        self.assertEqual(len(bookings(db, 3)), 2, "write skew: both transactions checked, saw no clash, and inserted")


class FixWithLock(unittest.TestCase):
    def test_prevents_double_booking(self):
        """book_with_lock: only one of two concurrent bookings of the same slot succeeds"""
        db = open_facility()
        results = run_concurrently(db, [
            lambda: book_with_lock(db, 3, SIX_PM, SEVEN_PM, "Ada"),
            lambda: book_with_lock(db, 3, SIX_PM, SEVEN_PM, "Grace"),
        ])
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(len(bookings(db, 3)), 1)
        self.assertTrue(any("FOR UPDATE" in s.upper() for s in statements(db)), "use SELECT ... FOR UPDATE")
        self.assertFalse(statements(db, "serializable"), "this fix uses the default READ COMMITTED isolation")

    def test_prevents_overlapping_ranges(self):
        """book_with_lock: 6:00-7:30 and 7:00-8:00 on the same bay can't both succeed"""
        db = open_facility()
        results = run_concurrently(db, [
            lambda: book_with_lock(db, 2, SIX_PM, SEVEN_PM + 30, "Ada"),
            lambda: book_with_lock(db, 2, SEVEN_PM, EIGHT_PM, "Grace"),
        ])
        self.assertEqual(sorted(results), [False, True])

    def test_many_customers(self):
        """book_with_lock: six customers racing for one slot get one booking"""
        db = open_facility()
        names = ["Ada", "Grace", "Linus", "Margaret", "Ken", "Barbara"]
        results = run_concurrently(db, [lambda n=n: book_with_lock(db, 1, SIX_PM, SEVEN_PM, n) for n in names])
        self.assertEqual(results.count(True), 1)
        self.assertEqual(len(bookings(db, 1)), 1)

    def test_only_locks_the_bay_being_booked(self):
        """book_with_lock: bookings of different bays don't wait for each other"""
        db = open_facility()
        start = time.perf_counter()
        results = run_concurrently(db, [
            lambda: book_with_lock(db, 1, SIX_PM, SEVEN_PM, "Ada"),
            lambda: book_with_lock(db, 2, SIX_PM, SEVEN_PM, "Grace"),
        ])
        self.assertEqual(results, [True, True])
        self.assertEqual(db.stats["lock_waits"], 0, "lock only the bay being booked, not every bay")
        self.assertLess(time.perf_counter() - start, 0.4)

    def test_back_to_back_slots(self):
        """book_with_lock: adjacent slots are fine, a taken slot is refused"""
        db = open_facility()
        self.assertTrue(book_with_lock(db, 4, SIX_PM, SEVEN_PM, "Ada"))
        self.assertTrue(book_with_lock(db, 4, SEVEN_PM, EIGHT_PM, "Grace"))
        self.assertFalse(book_with_lock(db, 4, SIX_PM + 30, SEVEN_PM + 30, "Linus"))


class FixWithSerializable(unittest.TestCase):
    def test_prevents_double_booking(self):
        """book_serializable: the database detects the conflict and the retry sees the booking"""
        db = open_facility()
        results = run_concurrently(db, [
            lambda: book_serializable(db, 3, SIX_PM, SEVEN_PM, "Ada"),
            lambda: book_serializable(db, 3, SIX_PM, SEVEN_PM, "Grace"),
        ])
        self.assertEqual(sorted(results), [False, True])
        self.assertEqual(len(bookings(db, 3)), 1)
        self.assertTrue(statements(db, "serializable"), 'use db.transaction(isolation="serializable")')
        self.assertFalse(any("FOR UPDATE" in s.upper() for s in statements(db, "serializable")), "no explicit locks: let serializable isolation catch it")
        self.assertGreaterEqual(db.stats["serialization_failures"], 1)

    def test_many_customers(self):
        """book_serializable: six customers racing for one slot get one booking"""
        db = open_facility()
        names = ["Ada", "Grace", "Linus", "Margaret", "Ken", "Barbara"]
        results = run_concurrently(db, [lambda n=n: book_serializable(db, 1, SIX_PM, SEVEN_PM, n) for n in names])
        self.assertEqual(results.count(True), 1)
        self.assertEqual(len(bookings(db, 1)), 1)

    def test_other_bays_dont_conflict(self):
        """book_serializable: bookings of different bays both commit first time"""
        db = open_facility()
        results = run_concurrently(db, [
            lambda: book_serializable(db, 1, SIX_PM, SEVEN_PM, "Ada"),
            lambda: book_serializable(db, 2, SIX_PM, SEVEN_PM, "Grace"),
        ])
        self.assertEqual(results, [True, True])
        self.assertEqual(db.stats["serialization_failures"], 0)

    def test_taken_slot(self):
        """book_serializable: refuses a slot that's already booked"""
        db = open_facility()
        self.assertTrue(book_serializable(db, 4, SIX_PM, SEVEN_PM, "Ada"))
        self.assertFalse(book_serializable(db, 4, SIX_PM, SEVEN_PM, "Grace"))


if __name__ == "__main__":
    unittest.main()
