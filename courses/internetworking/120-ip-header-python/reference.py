"""Reading, checking, and forwarding IPv4 headers, and building a ping."""

PROTOCOLS = {1: "ICMP", 6: "TCP", 17: "UDP"}

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0


def checksum(data):
    if len(data) % 2:
        data = data + b"\x00"
    s = 0
    for i in range(0, len(data), 2):
        s += (data[i] << 8) | data[i + 1]
        s = (s & 0xFFFF) + (s >> 16)
    return ~s & 0xFFFF


def _ip(b):
    return ".".join(str(x) for x in b)


def parse_header(raw):
    flags_frag = int.from_bytes(raw[6:8], "big")
    return {
        "version": raw[0] >> 4,
        "header_length": (raw[0] & 0x0F) * 4,
        "total_length": int.from_bytes(raw[2:4], "big"),
        "identification": int.from_bytes(raw[4:6], "big"),
        "dont_fragment": bool(raw[6] & 0x40),
        "more_fragments": bool(raw[6] & 0x20),
        "fragment_offset": (flags_frag & 0x1FFF) * 8,
        "ttl": raw[8],
        "protocol": PROTOCOLS.get(raw[9], "unknown"),
        "checksum": int.from_bytes(raw[10:12], "big"),
        "source": _ip(raw[12:16]),
        "destination": _ip(raw[16:20]),
    }


def header_ok(raw):
    length = (raw[0] & 0x0F) * 4
    return checksum(raw[:length]) == 0


def forward(raw):
    if raw[8] <= 1:
        return None
    out = bytearray(raw)
    out[8] -= 1
    out[10:12] = b"\x00\x00"
    length = (out[0] & 0x0F) * 4
    out[10:12] = checksum(bytes(out[:length])).to_bytes(2, "big")
    return bytes(out)


def echo_request(identifier, sequence, payload=b""):
    body = (identifier.to_bytes(2, "big") + sequence.to_bytes(2, "big") + payload)
    head = bytes([ICMP_ECHO_REQUEST, 0])
    c = checksum(head + b"\x00\x00" + body)
    return head + c.to_bytes(2, "big") + body
