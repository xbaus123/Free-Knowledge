"""A resilience toolkit: availability, series and parallel, RAID, parity rebuilds, and baselines."""

META_STATES = ["start-up", "idle", "normal", "busy", "failing", "failed"]

# level: (minimum drives, usable drives for n, drives that can fail for n)
RAID = {
    0: (2, lambda n: n, lambda n: 0),
    1: (2, lambda n: 1, lambda n: n - 1),
    5: (3, lambda n: n - 1, lambda n: 1),
    6: (4, lambda n: n - 2, lambda n: 2),
}


def availability(mtbf, mttr):
    if mtbf <= 0 or mttr < 0:
        raise ValueError("MTBF must be positive and MTTR not negative")
    return mtbf / (mtbf + mttr)


def downtime_minutes(avail, days=365):
    if not 0 <= avail <= 1:
        raise ValueError("availability must be between 0 and 1")
    return (1 - avail) * days * 24 * 60


def series(avails):
    if not avails:
        raise ValueError("no parts")
    total = 1.0
    for a in avails:
        total *= a
    return total


def parallel(avails):
    if not avails:
        raise ValueError("no parts")
    all_fail = 1.0
    for a in avails:
        all_fail *= 1 - a
    return 1 - all_fail


def _raid(level, drives):
    if level not in RAID:
        raise ValueError("unsupported RAID level: %r" % (level,))
    minimum, usable, tolerates = RAID[level]
    if drives < minimum:
        raise ValueError("RAID %d needs at least %d drives" % (level, minimum))
    return usable(drives), tolerates(drives)


def raid_usable(level, drives, size):
    return _raid(level, drives)[0] * size


def raid_tolerates(level, drives):
    return _raid(level, drives)[1]


def parity(blocks):
    if not blocks:
        raise ValueError("no blocks")
    length = len(blocks[0])
    out = bytearray(length)
    for b in blocks:
        if len(b) != length:
            raise ValueError("blocks must be the same length")
        for i, byte in enumerate(b):
            out[i] ^= byte
    return bytes(out)


def rebuild(blocks, parity_block):
    missing = [i for i, b in enumerate(blocks) if b is None]
    if len(missing) != 1:
        raise ValueError("exactly one block must be missing")
    return parity([b for b in blocks if b is not None] + [parity_block])


def check_reading(value, state, baselines):
    if state not in META_STATES:
        raise ValueError("unknown meta-state: %r" % (state,))
    if state not in baselines:
        raise ValueError("no baseline for " + state)
    low, high = baselines[state]
    if value < low:
        return "low"
    if value > high:
        return "high"
    return "ok"
