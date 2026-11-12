"""A VLSM planner: size subnets, split networks, and allocate largest first."""

ALL_ONES = 0xFFFFFFFF


def ip_to_int(text):
    a, b, c, d = (int(part) for part in text.split("."))
    return (a << 24) | (b << 16) | (c << 8) | d


def int_to_ip(n):
    return ".".join(str((n >> shift) & 0xFF) for shift in (24, 16, 8, 0))


def mask(prefix):
    return (ALL_ONES << (32 - prefix)) & ALL_ONES


def hosts_to_prefix(hosts):
    if hosts < 1:
        raise ValueError("need at least one host")
    for prefix in range(30, 0, -1):
        if 2 ** (32 - prefix) - 2 >= hosts:
            return prefix
    raise ValueError(f"{hosts} hosts won't fit in any IPv4 subnet")


def parse_cidr(cidr):
    ip, _, prefix = cidr.partition("/")
    if not prefix.isdigit() or not 0 <= int(prefix) <= 32:
        raise ValueError(f"bad prefix in {cidr!r}")
    prefix = int(prefix)
    n = ip_to_int(ip)
    if n & mask(prefix) != n:
        raise ValueError(f"{cidr!r} has host bits set")
    return n, prefix


def subnet_info(cidr):
    net, prefix = parse_cidr(cidr)
    size = 2 ** (32 - prefix)
    broadcast = net + size - 1
    return {
        "network": int_to_ip(net),
        "broadcast": int_to_ip(broadcast),
        "mask": int_to_ip(mask(prefix)),
        "gateway": int_to_ip(net + 1),
        "last_host": int_to_ip(broadcast - 1),
        "hosts": size - 2,
    }


def split(cidr, new_prefix):
    net, prefix = parse_cidr(cidr)
    if not prefix <= new_prefix <= 30:
        raise ValueError(f"can't split a /{prefix} into /{new_prefix}s")
    size = 2 ** (32 - new_prefix)
    return [f"{int_to_ip(net + i * size)}/{new_prefix}" for i in range(2 ** (new_prefix - prefix))]


def vlsm(cidr, needs):
    net, prefix = parse_cidr(cidr)
    end = net + 2 ** (32 - prefix)
    order = sorted(needs, key=lambda need: need[1], reverse=True)
    plan = []
    nxt = net
    for name, hosts in order:
        p = hosts_to_prefix(hosts)
        size = 2 ** (32 - p)
        start = (nxt + size - 1) // size * size  # round up to a multiple of the block size
        if p < prefix or start + size > end:
            raise ValueError(f"{name} ({hosts} hosts) doesn't fit in {cidr}")
        plan.append((name, f"{int_to_ip(start)}/{p}"))
        nxt = start + size
    return plan
