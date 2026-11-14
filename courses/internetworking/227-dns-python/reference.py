"""A resolver's toolkit: wire-format names, queries, reverse names, and lookups."""

import struct

QTYPES = {"A": 1, "NS": 2, "CNAME": 5, "SOA": 6, "PTR": 12, "MX": 15, "TXT": 16, "AAAA": 28, "AXFR": 252, "ANY": 255}
MAX_ALIASES = 8


def normalize(name):
    name = name.lower()
    return name if name.endswith(".") else name + "."


def encode_name(name):
    out = b""
    for label in normalize(name).split(".")[:-1]:
        if not label:
            continue
        raw = label.encode("ascii")
        if len(raw) > 63:
            raise ValueError("label too long: " + label)
        out += bytes([len(raw)]) + raw
    return out + b"\x00"


def build_query(query_id, name, qtype):
    header = struct.pack("!HHHHHH", query_id, 0x0100, 1, 0, 0, 0)
    return header + encode_name(name) + struct.pack("!HH", QTYPES[qtype.upper()], 1)


def reverse_name(ip):
    return ".".join(reversed(ip.split("."))) + ".in-addr.arpa."


def closest_zone(name, zones):
    labels = normalize(name).split(".")[:-1]
    best, best_len = None, -1
    for zone in zones:
        z = normalize(zone)
        zl = [] if z == "." else z.split(".")[:-1]
        if len(zl) <= len(labels) and labels[len(labels) - len(zl):] == zl and len(zl) > best_len:
            best, best_len = zone, len(zl)
    return best


def resolve(records, name, rtype):
    rtype = rtype.upper()
    current = normalize(name)
    for _ in range(MAX_ALIASES + 1):
        found = [v for n, t, v in records if normalize(n) == current and t.upper() == rtype]
        if found:
            return found
        aliases = [v for n, t, v in records if normalize(n) == current and t.upper() == "CNAME"]
        if not aliases:
            return []
        current = normalize(aliases[0])
    return []


def mail_hosts(records, domain):
    mx = []
    for value in resolve(records, domain, "MX"):
        priority, host = value.split()
        mx.append((int(priority), host))
    mx.sort(key=lambda pair: pair[0])
    return [host for _, host in mx]
