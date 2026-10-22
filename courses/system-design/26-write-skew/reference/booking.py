"""Booking golf simulator bays, safe under concurrency."""

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
    """Fix 1: READ COMMITTED plus an explicit lock on the bay's row.

    The booking we'd collide with doesn't exist yet, so there's nothing in
    bookings to lock. Every booking of a bay locks that bay's row first,
    so bookings of the same bay take turns, and other bays aren't held up.
    """
    with db.transaction() as tx:
        tx.execute("SELECT id FROM bays WHERE id = ? FOR UPDATE", (bay,))
        if tx.execute(OVERLAPS, (bay, end, start)):
            return False
        tx.execute(INSERT, (bay, start, end, customer))
        return True


def book_serializable(db, bay, start, end, customer, attempts=5):
    """Fix 2: SERIALIZABLE isolation, retrying when the database detects
    that a concurrent booking changed what we read."""
    for attempt in range(attempts):
        try:
            with db.transaction(isolation="serializable") as tx:
                if tx.execute(OVERLAPS, (bay, end, start)):
                    return False
                tx.execute(INSERT, (bay, start, end, customer))
                return True
        except SerializationFailure:
            if attempt == attempts - 1:
                raise
