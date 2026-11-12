import unittest

from solution import checksum, echo_request, forward, header_ok, parse_header

# The classic example header (Wikipedia, "IPv4 header checksum"):
# 192.168.0.1 -> 192.168.0.199, UDP, TTL 64, DF set, checksum 0xB861.
CLASSIC = bytes.fromhex("450000730000400040 11b861c0a80001c0a800c7".replace(" ", ""))

# A ping from the chapter's Mac to its hotspot: 172.20.10.2 -> 172.20.10.1.
PING = bytes.fromhex("450000541c46400040 01b237ac140a02ac140a01".replace(" ", ""))


def slow_checksum(data):
    """An independent version, adding everything first and folding after."""
    if len(data) % 2:
        data += b"\x00"
    s = sum(int.from_bytes(data[i:i + 2], "big") for i in range(0, len(data), 2))
    while s >> 16:
        s = (s & 0xFFFF) + (s >> 16)
    return ~s & 0xFFFF


class Checksum(unittest.TestCase):
    def test_classic_example(self):
        """The well-known example header's checksum is 0xB861"""
        zeroed = CLASSIC[:10] + b"\x00\x00" + CLASSIC[12:]
        self.assertEqual(checksum(zeroed), 0xB861)

    def test_valid_header_sums_to_zero(self):
        """A header with its correct checksum in place checks to 0"""
        self.assertEqual(checksum(CLASSIC), 0)
        self.assertEqual(checksum(PING), 0)

    def test_carry_folding(self):
        """Carries above 16 bits are folded back in"""
        self.assertEqual(checksum(b"\xff\xff\x00\x01"), 0xFFFE)
        self.assertEqual(checksum(b"\x80\x00\x80\x00\x80\x00"), 0x7FFE)

    def test_odd_length(self):
        """An odd byte at the end is padded with a zero"""
        self.assertEqual(checksum(b"\x01"), ~0x0100 & 0xFFFF)
        self.assertEqual(checksum(b"hello"), slow_checksum(b"hello"))

    def test_empty(self):
        """Nothing to add up"""
        self.assertEqual(checksum(b""), 0xFFFF)

    def test_matches_independent_version(self):
        """Agrees with a second implementation on assorted data"""
        for n in range(1, 60):
            data = bytes((i * 37 + n * 11) % 256 for i in range(n))
            with self.subTest(length=n):
                self.assertEqual(checksum(data), slow_checksum(data))


class Parse(unittest.TestCase):
    def test_classic(self):
        """Every field of the classic header"""
        self.assertEqual(parse_header(CLASSIC), {
            "version": 4, "header_length": 20, "total_length": 115, "identification": 0,
            "dont_fragment": True, "more_fragments": False, "fragment_offset": 0, "ttl": 64,
            "protocol": "UDP", "checksum": 0xB861, "source": "192.168.0.1", "destination": "192.168.0.199",
        })

    def test_ping(self):
        """The hotspot ping: ICMP between two 172.20.10.x hosts"""
        h = parse_header(PING)
        self.assertEqual(h["protocol"], "ICMP")
        self.assertEqual(h["total_length"], 84)
        self.assertEqual(h["identification"], 0x1C46)
        self.assertEqual((h["source"], h["destination"]), ("172.20.10.2", "172.20.10.1"))

    def test_fragment(self):
        """MF set, offset 185 units = 1480 bytes, protocol TCP"""
        raw = bytearray(CLASSIC)
        raw[6:8] = (0x2000 | 185).to_bytes(2, "big")
        raw[9] = 6
        h = parse_header(bytes(raw))
        self.assertTrue(h["more_fragments"])
        self.assertFalse(h["dont_fragment"])
        self.assertEqual(h["fragment_offset"], 1480)
        self.assertEqual(h["protocol"], "TCP")

    def test_options_and_unknown_protocol(self):
        """IHL 6 means 24 bytes; protocol 99 isn't in the table"""
        raw = bytearray(CLASSIC) + b"\x00\x00\x00\x00"
        raw[0] = 0x46
        raw[9] = 99
        h = parse_header(bytes(raw))
        self.assertEqual(h["header_length"], 24)
        self.assertEqual(h["protocol"], "unknown")


class HeaderOk(unittest.TestCase):
    def test_good(self):
        """Correct headers pass"""
        self.assertTrue(header_ok(CLASSIC))
        self.assertTrue(header_ok(PING))

    def test_flipped_bit(self):
        """One flipped bit anywhere in the header is caught"""
        for byte in range(20):
            raw = bytearray(CLASSIC)
            raw[byte] ^= 0x04
            with self.subTest(byte=byte):
                self.assertFalse(header_ok(bytes(raw)))

    def test_only_checks_header(self):
        """Data after the header doesn't affect the header checksum"""
        self.assertTrue(header_ok(CLASSIC + b"any payload at all"))


class Forward(unittest.TestCase):
    def test_decrements_ttl(self):
        """TTL goes down by one and the checksum is recomputed"""
        out = forward(CLASSIC)
        self.assertEqual(out[8], 63)
        self.assertTrue(header_ok(out))
        self.assertEqual(out[:8], CLASSIC[:8])
        self.assertEqual(out[12:], CLASSIC[12:])

    def test_keeps_payload(self):
        """The data after the header is untouched"""
        out = forward(PING + b"payload")
        self.assertTrue(out.endswith(b"payload"))
        self.assertEqual(len(out), len(PING) + 7)

    def test_many_hops(self):
        """Forward 63 times: TTL 1, still valid; once more and it's dropped"""
        raw = CLASSIC
        for _ in range(63):
            raw = forward(raw)
            self.assertTrue(header_ok(raw))
        self.assertEqual(raw[8], 1)
        self.assertIsNone(forward(raw))

    def test_does_not_modify_input(self):
        """The original bytes are left alone"""
        before = bytes(CLASSIC)
        forward(CLASSIC)
        self.assertEqual(CLASSIC, before)


class Echo(unittest.TestCase):
    def test_layout(self):
        """Type 8, code 0, then identifier, sequence, and payload"""
        msg = echo_request(0x1234, 7, b"hi")
        self.assertEqual(msg[0], 8)
        self.assertEqual(msg[1], 0)
        self.assertEqual(msg[4:6], b"\x12\x34")
        self.assertEqual(msg[6:8], b"\x00\x07")
        self.assertEqual(msg[8:], b"hi")
        self.assertEqual(len(msg), 10)

    def test_known_bytes(self):
        """Identifier 1, sequence 0, payload "hi" """
        self.assertEqual(echo_request(1, 0, b"hi").hex(), "08008f95000100006869")

    def test_checksum_verifies(self):
        """The whole message checks to 0, even with an odd-length payload"""
        for payload in [b"", b"x", b"abcdefgh" * 7, bytes(56)]:
            with self.subTest(payload=payload):
                self.assertEqual(checksum(echo_request(42, 3, payload)), 0)

    def test_default_payload(self):
        """No payload: just the 8-byte header"""
        self.assertEqual(len(echo_request(1, 1)), 8)


if __name__ == "__main__":
    unittest.main()
