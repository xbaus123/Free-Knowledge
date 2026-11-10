"""Signal budget: the physical layer's arithmetic.

Attenuation in decibels, how far a signal can go before it's too weak,
how many repeaters a long run needs, how long a transfer takes, and
which cable to buy for the job.
"""

import math

# A small, made-up but realistic catalog of cables.
MEDIA = [
    {"name": "UTP Cat 6", "max_segment_m": 100, "mbps": 1000, "emi_resistant": False, "cost_per_m": 0.5},
    {"name": "STP Cat 6a", "max_segment_m": 100, "mbps": 10000, "emi_resistant": True, "cost_per_m": 1.2},
    {"name": "Broadband coax", "max_segment_m": 500, "mbps": 1000, "emi_resistant": True, "cost_per_m": 0.8},
    {"name": "Multimode fiber", "max_segment_m": 550, "mbps": 10000, "emi_resistant": True, "cost_per_m": 2.0},
    {"name": "Single-mode fiber", "max_segment_m": 10000, "mbps": 100000, "emi_resistant": True, "cost_per_m": 3.0},
]


def db_loss(power_in, power_out):
    """Loss in decibels between the power sent and the power received."""
    if power_in <= 0 or power_out <= 0:
        raise ValueError("power must be positive")
    return 10 * math.log10(power_in / power_out)


def power_after(power_in, db_per_100m, length_m):
    """Power left after length_m meters of cable that loses db_per_100m per 100 m."""
    loss = db_per_100m * length_m / 100
    return power_in / 10 ** (loss / 10)


def max_segment(power_in, min_power, db_per_100m):
    """Longest cable, in meters, that still delivers at least min_power."""
    if db_per_100m <= 0:
        raise ValueError("attenuation must be positive")
    if min_power >= power_in:
        return 0.0
    return 100 * db_loss(power_in, min_power) / db_per_100m


def repeaters_needed(distance_m, segment_m):
    """Repeaters needed to cover distance_m with segments of at most segment_m."""
    if segment_m <= 0:
        raise ValueError("segment length must be positive")
    if distance_m <= segment_m:
        return 0
    return math.ceil(distance_m / segment_m) - 1


def transfer_seconds(size_bytes, mbps):
    """Seconds to send size_bytes over a link of mbps megabits per second."""
    return size_bytes * 8 / (mbps * 1_000_000)


def choose_medium(media, distance_m, min_mbps, noisy):
    """Name of the cheapest medium that covers distance_m in one segment."""
    best = None
    for medium in media:
        if medium["max_segment_m"] < distance_m:
            continue
        if medium["mbps"] < min_mbps:
            continue
        if noisy and not medium["emi_resistant"]:
            continue
        cost = medium["cost_per_m"] * distance_m
        if best is None or cost < best[0]:
            best = (cost, medium["name"])
    return None if best is None else best[1]
