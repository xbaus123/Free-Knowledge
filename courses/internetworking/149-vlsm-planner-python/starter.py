"""A VLSM planner: size subnets, split networks, and allocate largest first."""

ALL_ONES = 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Helpers you wrote in chapter 4, done for you.


def ip_to_int(text):
    a, b, c, d = (int(part) for part in text.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def int_to_ip(n):
    return ".".join(str((n >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def mask(prefix):
    """The mask for a prefix length, as a 32-bit integer."""
    return (ALL_ONES << (32 - prefix)) & ALL_ONES


# ---------------------------------------------------------------------------
# Part 1: sizing


def hosts_to_prefix(hosts):
    """The smallest subnet that holds this many hosts: 50 -> 26, 2 -> 30.

    Find the longest prefix (start at 30 and work down) where
    2 ** (32 - prefix) - 2 >= hosts. Raise ValueError if hosts < 1.
    """
    # TODO
    pass


def parse_cidr(cidr):
    """"10.1.1.64/26" -> (ip_to_int("10.1.1.64"), 26).

    Raise ValueError if the prefix isn't a whole number from 0 to 32, or if
    the address has host bits set (it isn't the network address), as in
    "10.1.1.8/28".
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 2: one subnet


def subnet_info(cidr):
    """Everything about one subnet, as a dict of strings (and an int):

    subnet_info("166.23.9.16/28") == {
        "network": "166.23.9.16",
        "broadcast": "166.23.9.31",
        "mask": "255.255.255.240",
        "gateway": "166.23.9.17",      # first usable, by convention
        "last_host": "166.23.9.30",
        "hosts": 14,
    }
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 3: many subnets


def split(cidr, new_prefix):
    """Fixed-length subnetting: split("10.1.1.0/24", 26) ->
    ["10.1.1.0/26", "10.1.1.64/26", "10.1.1.128/26", "10.1.1.192/26"].

    Use every subnet (subnet zero and the all-ones subnet included).
    Raise ValueError unless prefix <= new_prefix <= 30.
    """
    # TODO
    pass


def vlsm(cidr, needs):
    """Allocate subnets largest first.

    needs is a list of (name, hosts). Return a list of (name, "a.b.c.d/p")
    in allocation order: most hosts first (ties keep their input order).
    Start at the network address; each block goes at the next address that's
    a multiple of its own size. Raise ValueError if anything doesn't fit.
    """
    # TODO
    pass


if __name__ == "__main__":
    print(hosts_to_prefix(100))                    # 25
    print(subnet_info("166.21.16.0/20"))
    print(split("10.1.1.0/24", 26))
    for name, net in vlsm("10.1.1.0/24", [("link", 2), ("staff", 100), ("lab", 50)]) or []:
        print(name, net)                           # staff 10.1.1.0/25, lab 10.1.1.128/26, link 10.1.1.192/30
