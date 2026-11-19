"""The facility's database. (Read-only.)"""

from minidb import Database


def open_facility(bays=4):
    """A database with `bays` simulator bays and no bookings yet.

    bays(id, name)
    bookings(id, bay_id, start_min, end_min, customer)

    Times are minutes after midnight: 18:00 is 1080. A booking covers
    [start_min, end_min), so 18:00-19:00 and 19:00-20:00 don't overlap.
    """
    db = Database()
    db.create_table("bays", ["name"])
    db.create_table("bookings", ["bay_id", "start_min", "end_min", "customer"])
    for i in range(1, bays + 1):
        db.insert("bays", name=f"Bay {i}")
    return db
