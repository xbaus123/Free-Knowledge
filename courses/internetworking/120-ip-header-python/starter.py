"""Reading, checking, and forwarding IPv4 headers, and building a ping."""

PROTOCOLS = {1: "ICMP", 6: "TCP", 17: "UDP"}

ICMP_ECHO_REQUEST = 8
ICMP_ECHO_REPLY = 0


def checksum(data):
    """The Internet checksum (RFC 1071) of some bytes.

    1. Pad an odd-length input with one zero byte.
    2. Add up the 16-bit big-endian words.
    3. Fold any carry above 16 bits back in: s = (s & 0xFFFF) + (s >> 16)
    4. Return the ones' complement: ~s & 0xFFFF
    """
    # TODO
    pass


def parse_header(raw):
    """Read an IPv4 header from raw bytes. Return a dictionary:

        {
            "version": 4,
            "header_length": 20,          # IHL * 4, in bytes
            "total_length": 84,
            "identification": 0x1C46,
            "dont_fragment": True,        # byte 6 & 0x40
            "more_fragments": False,      # byte 6 & 0x20
            "fragment_offset": 0,         # low 13 bits of bytes 6-7, times 8
            "ttl": 64,
            "protocol": "ICMP",           # PROTOCOLS name, or "unknown"
            "checksum": 0xB237,           # the field as it is, not recomputed
            "source": "172.20.10.2",
            "destination": "172.20.10.1",
        }
    """
    # TODO
    pass


def header_ok(raw):
    """True if the checksum over the first IHL * 4 bytes comes out 0."""
    # TODO
    pass


def forward(raw):
    """What a router does: return a copy with TTL - 1 and a new checksum.

    Return None if the TTL is 1 or less (it would reach 0: drop it).
    To recompute, set bytes 10-11 to zero, take the checksum of the
    header, and write it back big-endian. Keep any data after the header.
    """
    # TODO
    pass


def echo_request(identifier, sequence, payload=b""):
    """An ICMP Echo Request: type 8, code 0, checksum (2 bytes),
    identifier (2 bytes), sequence (2 bytes), then the payload.

    Compute the checksum over the whole message with the checksum
    field set to zero.
    """
    # TODO
    pass


if __name__ == "__main__":
    header = bytes.fromhex("45000054 1c464000 40010000 ac140a02 ac140a01")
    c = checksum(header)
    if c is None:
        print("Write checksum() first.")
    else:
        print(hex(c))  # 0xb237: put it in bytes 10-11 and the header checks out
        good = header[:10] + c.to_bytes(2, "big") + header[12:]
        print(parse_header(good))
        print(header_ok(good))
        print(forward(good))
    print(echo_request(1, 0, b"hi"))
