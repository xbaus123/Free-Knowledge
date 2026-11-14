"""A wireless toolkit: 2.4 GHz channels, path loss, DSSS, frequency hopping, and usage tiers."""
import math

BARKER = [1, 0, 1, 1, 0, 1, 1, 1, 0, 0, 0]

WALL_LOSS_DB = {"drywall": 3, "glass": 4, "brick": 8, "concrete": 12, "metal": 20}


# ---------------------------------------------------------------------------
# Part 1: 2.4 GHz channels


def center_mhz(channel):
    """Center frequency of a 2.4 GHz channel, in MHz.

    Channels 1 to 13 are 2407 + 5 * channel. Channel 14 is 2484.
    center_mhz(6) == 2437
    Raise ValueError for any other channel.
    """
    # TODO
    pass


def overlaps(a, b):
    """True if the channels' centers are less than 22 MHz apart.

    overlaps(1, 6) is False, overlaps(1, 3) is True.
    """
    # TODO
    pass


def best_channel(neighbors):
    """Pick 1, 6, or 11: whichever overlaps the fewest neighbor channels.

    best_channel([1, 1, 6]) == 11. Ties go to the first of 1, 6, 11.
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 2: path loss


def fspl_db(distance_m, freq_mhz):
    """Free-space path loss in dB:
    20 * log10(distance_m) + 20 * log10(freq_mhz) - 27.55

    fspl_db(10, 2437) is about 60.19
    Raise ValueError unless both are positive.
    """
    # TODO
    pass


def received_dbm(tx_dbm, distance_m, freq_mhz, walls=()):
    """Transmit power minus path loss minus each wall's loss from WALL_LOSS_DB.

    received_dbm(20, 10, 2437, ["drywall", "concrete"]) is about -55.19
    Raise ValueError for a material that isn't in the table.
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 3: DSSS


def spread(bits):
    """Each 1 becomes BARKER, each 0 becomes BARKER inverted.

    spread([1]) == BARKER
    Raise ValueError for anything but 0 or 1.
    """
    # TODO
    pass


def despread(chips):
    """Each group of 11 chips becomes 1 if more than half match BARKER, else 0.

    despread(spread([1, 0])) == [1, 0]
    Raise ValueError if the chip count isn't a multiple of 11.
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 4: frequency hopping


def hop_sequence(seed, hops, channels=79):
    """`hops` channels from the generator x = (1103515245 * x + 12345) % 2**31.

    Start with x = seed. For each hop, step x first, then use x % channels.
    hop_sequence(42, 5) == [50, 32, 27, 71, 57]
    Raise ValueError if hops is negative or channels is less than 1.
    """
    # TODO
    pass


def jammed_fraction(sequence, jammed):
    """The fraction of hops in `sequence` that land on a jammed channel.

    jammed_fraction([3, 7, 3, 9], [3]) == 0.5
    Raise ValueError for an empty sequence.
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 5: usage


def usage_tier(mbps):
    """"light" up to 25 Mbps, "medium" up to 300, "heavy" above that.

    Raise ValueError for negative bandwidth.
    """
    # TODO
    pass


if __name__ == "__main__":
    print(center_mhz(6), overlaps(1, 6), overlaps(1, 3))   # 2437 False True
    print(best_channel([1, 1, 6]))                       # 11
    print(fspl_db(10, 2437))                             # about 60.19
    print(received_dbm(20, 10, 2437, ["drywall", "concrete"]))  # about -55.19
    chips = spread([1, 0]) or []
    if chips:
        chips[0] ^= 1                                    # noise flips a chip
    print(despread(chips))                               # [1, 0]
    print(hop_sequence(42, 5))                           # [50, 32, 27, 71, 57]
    print(jammed_fraction([3, 7, 3, 9], [3]))            # 0.5
    print(usage_tier(120))                               # medium
