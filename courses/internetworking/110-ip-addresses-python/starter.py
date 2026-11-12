"""A subnet calculator: IPv4 addresses as 32-bit integers."""

ALL_ONES = 0xFFFFFFFF

# RFC 1918 private ranges, as (network, prefix length).
PRIVATE_RANGES = [("10.0.0.0", 8), ("172.16.0.0", 12), ("192.168.0.0", 16)]


# ---------------------------------------------------------------------------
# Part 1: converting


def ip_to_int(text):
    """"192.168.1.15" -> 3232235791.

    Shift the running total left 8 bits and OR in each octet. Raise
    ValueError unless there are exactly four parts, each made of digits,
    each from 0 to 255.
    """
    # TODO
    pass


def int_to_ip(n):
    """3232235791 -> "192.168.1.15". Each octet is (n >> shift) & 0xFF."""
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 2: what kind of address is it?


def address_class(ip):
    """"A" (first octet 0-127), "B" (128-191), "C" (192-223),
    "D" (224-239), or "E" (240-255)."""
    # TODO
    pass


def is_private(ip):
    """True if ip is in one of PRIVATE_RANGES (RFC 1918)."""
    # TODO
    pass


def is_loopback(ip):
    """True if ip is on the 127 network."""
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 3: masks and subnets


def prefix_to_mask(prefix):
    """24 -> "255.255.255.0". The mask is (ALL_ONES << (32 - prefix)) & ALL_ONES."""
    # TODO
    pass


def mask_to_prefix(mask):
    """"255.255.252.0" -> 22. Raise ValueError if the 1s aren't all at the
    front, as in "255.0.255.0"."""
    # TODO
    pass


def network_address(ip, prefix):
    """("192.168.10.77", 26) -> "192.168.10.64": the address AND the mask."""
    # TODO
    pass


def broadcast_address(ip, prefix):
    """("192.168.10.77", 26) -> "192.168.10.127": every host bit set to 1."""
    # TODO
    pass


def usable_hosts(prefix):
    """2 ** host_bits - 2, but a /31 has 2 and a /32 has 1."""
    # TODO
    pass


def same_subnet(a, b, prefix):
    """True if a and b are on the same network under this prefix."""
    # TODO
    pass


if __name__ == "__main__":
    print(ip_to_int("192.168.1.15"))                 # 3232235791
    print(address_class("10.104.216.118"))           # A
    print(network_address("10.104.216.118", 22))     # 10.104.216.0
    print(broadcast_address("10.104.216.118", 22))   # 10.104.219.255
    print(usable_hosts(22))                          # 1022
