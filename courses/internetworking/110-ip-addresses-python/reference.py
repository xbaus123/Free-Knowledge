"""A subnet calculator: IPv4 addresses as 32-bit integers."""

ALL_ONES = 0xFFFFFFFF

# RFC 1918 private ranges, as (network, prefix length).
PRIVATE_RANGES = [("10.0.0.0", 8), ("172.16.0.0", 12), ("192.168.0.0", 16)]


def ip_to_int(text):
    parts = text.split(".")
    if len(parts) != 4:
        raise ValueError(f"not an IPv4 address: {text!r}")
    n = 0
    for part in parts:
        if not part.isdigit() or not part.isascii() or int(part) > 255:
            raise ValueError(f"bad octet {part!r} in {text!r}")
        n = (n << 8) | int(part)
    return n


def int_to_ip(n):
    return ".".join(str((n >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def address_class(ip):
    first = ip_to_int(ip) >> 24
    if first < 128:
        return "A"
    if first < 192:
        return "B"
    if first < 224:
        return "C"
    if first < 240:
        return "D"
    return "E"


def _mask(prefix):
    return (ALL_ONES << (32 - prefix)) & ALL_ONES


def is_private(ip):
    n = ip_to_int(ip)
    return any(n & _mask(p) == ip_to_int(net) for net, p in PRIVATE_RANGES)


def is_loopback(ip):
    return ip_to_int(ip) >> 24 == 127


def prefix_to_mask(prefix):
    return int_to_ip(_mask(prefix))


def mask_to_prefix(mask):
    n = ip_to_int(mask)
    prefix = bin(n).count("1")
    if _mask(prefix) != n:
        raise ValueError(f"not a valid subnet mask: {mask!r}")
    return prefix


def network_address(ip, prefix):
    return int_to_ip(ip_to_int(ip) & _mask(prefix))


def broadcast_address(ip, prefix):
    return int_to_ip(ip_to_int(ip) | (~_mask(prefix) & ALL_ONES))


def usable_hosts(prefix):
    if prefix == 32:
        return 1
    if prefix == 31:
        return 2
    return 2 ** (32 - prefix) - 2


def same_subnet(a, b, prefix):
    m = _mask(prefix)
    return ip_to_int(a) & m == ip_to_int(b) & m
