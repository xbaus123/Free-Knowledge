"""Error detection and Ethernet frames: parity, CRC by hand, and a real FCS."""

import zlib

ETHERTYPE_IPV4 = 0x0800
ETHERTYPE_ARP = 0x0806
ETHERTYPE_IPV6 = 0x86DD


# ---------------------------------------------------------------------------
# Part 1: parity and CRC on bit strings like "101110"


def parity_bit(bits):
    """The even parity bit for a string of '0' and '1' characters.

    parity_bit("1011001") == "0"   (four 1s, already even)
    parity_bit("1110000") == "1"   (three 1s)
    Raise ValueError if bits contains anything other than '0' and '1'.
    """
    # TODO
    pass


def crc_remainder(data, generator):
    """The r CRC bits R for data and a generator G of r + 1 bits.

    Append r zeros to data, then do mod-2 long division by generator:
    wherever the leading bit is 1, XOR the generator in.
    The last r bits are the remainder.

    crc_remainder("101110", "1001") == "011"
    Raise ValueError if either argument isn't a bit string, or if the
    generator is shorter than 2 bits or doesn't start with '1'.
    """
    # TODO
    pass


def crc_encode(data, generator):
    """The bits to send: data followed by its CRC bits."""
    # TODO
    pass


def crc_check(codeword, generator):
    """True if codeword divides by generator with a remainder of all zeros."""
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 2: real Ethernet II frames, as bytes


def build_frame(dst, src, ethertype, payload):
    """Build an Ethernet II frame.

    dst and src are MAC addresses like "3c:bd:c5:40:77:61".
    ethertype is an int such as ETHERTYPE_IPV4; write it as 2 bytes, big-endian.
    payload is bytes. Pad it with zero bytes up to 46 bytes. Raise
    ValueError if it's longer than 1500 bytes.
    Finish with the 4-byte FCS: zlib.crc32() of everything before it,
    written little-endian: zlib.crc32(body).to_bytes(4, "little")
    """
    # TODO
    pass


def parse_frame(frame):
    """Take an Ethernet II frame (bytes) apart.

    Return a dictionary:
        "dst":       destination MAC as "aa:bb:cc:dd:ee:ff"
        "src":       source MAC, the same way
        "ethertype": an int
        "payload":   the bytes between the header and the FCS (padding included)
        "fcs_ok":    True if the FCS matches the rest of the frame
    Raise ValueError for a runt (under 64 bytes) or a frame over 1518 bytes.
    """
    # TODO
    pass


if __name__ == "__main__":
    print(crc_remainder("101110", "1001"))
    frame = build_frame("ff:ff:ff:ff:ff:ff", "3c:22:fb:45:a4:85", ETHERTYPE_ARP, b"who has 192.168.1.1?")
    if frame:
        print(len(frame), "bytes:", frame.hex(" "))
        print(parse_frame(frame))
