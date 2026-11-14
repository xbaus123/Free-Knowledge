"""A resilience toolkit: availability, series and parallel, RAID, parity rebuilds, and baselines."""

META_STATES = ["start-up", "idle", "normal", "busy", "failing", "failed"]


# ---------------------------------------------------------------------------
# Part 1: availability


def availability(mtbf, mttr):
    """MTBF / (MTBF + MTTR).

    availability(99, 1) == 0.99
    Raise ValueError if mtbf isn't positive or mttr is negative.
    """
    # TODO
    pass


def downtime_minutes(avail, days=365):
    """Minutes of downtime the availability allows over that many days.

    downtime_minutes(0.999) is about 525.6
    Raise ValueError unless 0 <= avail <= 1.
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 2: series and parallel


def series(avails):
    """Every part must work: multiply.

    series([0.99, 0.99]) is about 0.9801
    Raise ValueError for an empty list.
    """
    # TODO
    pass


def parallel(avails):
    """Any one part is enough: it fails only if all of them fail.

    parallel([0.99, 0.99]) is about 0.9999
    Raise ValueError for an empty list.
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 3: RAID (levels 0, 1, 5, and 6)


def raid_usable(level, drives, size):
    """Usable space of an array of `drives` drives, each `size` big.

    raid_usable(5, 4, 2) == 6
    Raise ValueError for another level, or too few drives
    (2 for RAID 0 and 1, 3 for RAID 5, 4 for RAID 6).
    """
    # TODO
    pass


def raid_tolerates(level, drives):
    """How many drives can fail without losing data.

    raid_tolerates(1, 3) == 2
    Same errors as raid_usable.
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 4: rebuilding with parity


def parity(blocks):
    """XOR equal-length bytes blocks together, byte by byte.

    parity([b"\\x0f", b"\\xf0"]) == b"\\xff"
    Raise ValueError for no blocks, or blocks of different lengths.
    """
    # TODO
    pass


def rebuild(blocks, parity_block):
    """Exactly one of blocks is None. Return the missing block.

    rebuild([b"\\x0f", None], b"\\xff") == b"\\xf0"
    Raise ValueError unless exactly one block is None.
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 5: baselines


def check_reading(value, state, baselines):
    """Compare a reading to its meta-state's (low, high) range, inclusive.

    Return "low", "ok", or "high". Raise ValueError if state isn't one of
    META_STATES, or has no baseline.
    """
    # TODO
    pass


if __name__ == "__main__":
    print(availability(99, 1))                       # 0.99
    print(downtime_minutes(0.999))                   # about 525.6
    print(series([0.99, 0.99]))                      # about 0.9801
    print(parallel([0.99, 0.99]))                    # about 0.9999
    print(raid_usable(5, 4, 2), raid_tolerates(5, 4))  # 6 1
    data = [b"web", b"app", b"db!"]
    print(rebuild([b"web", None, b"db!"], parity(data)))  # b'app'
    cpu = {"idle": (1, 5), "normal": (20, 50), "busy": (60, 90)}
    print(check_reading(70, "idle", cpu))            # high
