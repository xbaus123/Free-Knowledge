"""A wireless toolkit: 2.4 GHz channels, path loss, DSSS, frequency hopping, and usage tiers."""
import math

BARKER = [1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0]

WALL_LOSS_DB = {"drywall": 3, "glass": 4, "brick": 8, "concrete": 12, "metal": 20}


def center_mhz(channel):
    if channel == 14:
        return 2484
    if isinstance(channel, int) and 1 <= channel <= 13:
        return 2407 + 5 * channel
    raise ValueError("no such 2.4 GHz channel: %r" % (channel,))


def overlaps(a, b):
    return abs(center_mhz(a) - center_mhz(b)) < 22


def best_channel(neighbors):
    counts = {}
    for candidate in (1, 6, 11):
        counts[candidate] = sum(1 for n in neighbors if overlaps(candidate, n))
    return min((1, 6, 11), key=lambda c: counts[c])


def fspl_db(distance_m, freq_mhz):
    if distance_m <= 0 or freq_mhz <= 0:
        raise ValueError("distance and frequency must be positive")
    return 20 * math.log10(distance_m) + 20 * math.log10(freq_mhz) - 27.55


def received_dbm(tx_dbm, distance_m, freq_mhz, walls=()):
    loss = fspl_db(distance_m, freq_mhz)
    for wall in walls:
        if wall not in WALL_LOSS_DB:
            raise ValueError("unknown material: %r" % (wall,))
        loss += WALL_LOSS_DB[wall]
    return tx_dbm - loss


def spread(bits):
    chips = []
    for bit in bits:
        if bit not in (0, 1):
            raise ValueError("bits must be 0 or 1")
        chips.extend(BARKER if bit == 1 else [1 - c for c in BARKER])
    return chips


def despread(chips):
    n = len(BARKER)
    if len(chips) % n:
        raise ValueError("chip count must be a multiple of %d" % n)
    bits = []
    for i in range(0, len(chips), n):
        matches = sum(1 for c, b in zip(chips[i:i + n], BARKER) if c == b)
        bits.append(1 if matches > n // 2 else 0)
    return bits


def hop_sequence(seed, hops, channels=79):
    if hops < 0 or channels < 1:
        raise ValueError("hops can't be negative and channels must be at least 1")
    x = seed
    out = []
    for _ in range(hops):
        x = (1103515245 * x + 12345) % 2 ** 31
        out.append(x % channels)
    return out


def jammed_fraction(sequence, jammed):
    if not sequence:
        raise ValueError("empty sequence")
    jammed = set(jammed)
    return sum(1 for ch in sequence if ch in jammed) / len(sequence)


def usage_tier(mbps):
    if mbps < 0:
        raise ValueError("bandwidth can't be negative")
    if mbps <= 25:
        return "light"
    if mbps <= 300:
        return "medium"
    return "heavy"
