"""Booking golf simulator bays.

Two customers clicking "Book" for the same bay and time at the same
moment can both get it: each transaction checks for an overlapping
booking, sees none, and inserts its own. Fix it twice.
"""

from minidb import SerializationFailure

OVERLAPS = "SELECT id FROM bookings WHERE bay_id = ? AND start_min < ? AND end_min > ?"
INSERT = "INSERT INTO bookings (bay_id, start_min, end_min, customer) VALUES (?, ?, ?, ?)"


def book_unsafe(db, bay, start, end, customer):
    """The original flow: check, then insert. Don't change this one; the
    tests use it to reproduce the bug."""
    with db.transaction() as tx:
        if tx.execute(OVERLAPS, (bay, end, start)):
            return False
        tx.execute(INSERT, (bay, start, end, customer))
        return True


def book_with_lock(db, bay, start, end, customer):
    """Fix 1: READ COMMITTED plus an explicit lock.

    TODO: before checking for overlaps, lock something that every booking
    of this bay must also lock, with SELECT ... FOR UPDATE. (The booking
    you'd collide with doesn't exist yet, so there's no booking row to
    lock.)
    """
    with db.transaction() as tx:
        if tx.execute(OVERLAPS, (bay, end, start)):
            return False
        tx.execute(INSERT, (bay, start, end, customer))
        return True


def book_serializable(db, bay, start, end, customer, attempts=5):
    """Fix 2: SERIALIZABLE isolation, no explicit locks.

    TODO: run the transaction with isolation="serializable". The
    database may refuse to commit with SerializationFailure if a
    concurrent booking changed what you read: retry from the start, up
    to `attempts` times, then let the error propagate.
    """
    with db.transaction() as tx:
        if tx.execute(OVERLAPS, (bay, end, start)):
            return False
        tx.execute(INSERT, (bay, start, end, customer))
        return True
