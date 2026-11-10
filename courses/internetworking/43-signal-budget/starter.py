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
    """Loss in decibels between the power sent and the power received.

    loss = 10 * log10(power_in / power_out)
    Raise ValueError if either power is zero or negative.
    """
    # TODO
    pass


def power_after(power_in, db_per_100m, length_m):
    """Power left after length_m meters of cable that loses db_per_100m per 100 m.

    First work out the total loss in dB, then turn it back into a
    power ratio: power_out = power_in / 10 ** (loss / 10)
    """
    # TODO
    pass


def max_segment(power_in, min_power, db_per_100m):
    """Longest cable, in meters, that still delivers at least min_power.

    Return 0.0 if min_power is already >= power_in.
    Raise ValueError if db_per_100m is zero or negative.
    """
    # TODO
    pass


def repeaters_needed(distance_m, segment_m):
    """Repeaters needed to cover distance_m with segments of at most segment_m.

    A run that fits in one segment needs none. Raise ValueError if
    segment_m is zero or negative.
    """
    # TODO
    pass


def transfer_seconds(size_bytes, mbps):
    """Seconds to send size_bytes over a link of mbps megabits per second.

    Careful: the size is in bytes, the speed is in bits.
    """
    # TODO
    pass


def choose_medium(media, distance_m, min_mbps, noisy):
    """Name of the cheapest medium that covers distance_m in one segment.

    A medium qualifies if its max_segment_m reaches distance_m, its mbps
    is at least min_mbps, and, when noisy is True, it's emi_resistant.
    The cost is cost_per_m * distance_m. On a tie, pick the one that
    comes first in the list. Return None if nothing qualifies.
    """
    # TODO
    pass


if __name__ == "__main__":
    # Try things out with Run.
    print(db_loss(100, 50))
    print(choose_medium(MEDIA, 80, 500, noisy=True))
