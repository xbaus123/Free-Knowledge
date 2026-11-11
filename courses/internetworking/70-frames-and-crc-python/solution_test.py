import unittest
import zlib

from solution import (
    ETHERTYPE_ARP,
    ETHERTYPE_IPV4,
    ETHERTYPE_IPV6,
    build_frame,
    crc_check,
    crc_encode,
    crc_remainder,
    parity_bit,
    parse_frame,
)

SRC = "3c:22:fb:45:a4:85"
GW = "3c:bd:c5:40:77:61"
BCAST = "ff:ff:ff:ff:ff:ff"


class Parity(unittest.TestCase):
    def test_even_already(self):
        """Four 1s is already even: parity bit 0"""
        self.assertEqual(parity_bit("1011001"), "0")

    def test_odd(self):
        """Three 1s: parity bit 1"""
        self.assertEqual(parity_bit("1110000"), "1")

    def test_reading_example(self):
        """The reading's 16-bit example has nine 1s"""
        self.assertEqual(parity_bit("0111000110101011"), "1")

    def test_empty(self):
        """No bits, no 1s: parity bit 0"""
        self.assertEqual(parity_bit(""), "0")

    def test_rejects_non_bits(self):
        """Anything but 0 and 1 raises ValueError"""
        with self.assertRaises(ValueError):
            parity_bit("10201")


class CrcRemainder(unittest.TestCase):
    def test_reading_example(self):
        """D = 101110, G = 1001 gives R = 011"""
        self.assertEqual(crc_remainder("101110", "1001"), "011")

    def test_quiz_examples(self):
        """The examples from the CRC check"""
        self.assertEqual(crc_remainder("1101", "1011"), "001")
        self.assertEqual(crc_remainder("110101", "101"), "11")
        self.assertEqual(crc_remainder("1011", "11"), "1")

    def test_remainder_length(self):
        """R always has r = len(G) - 1 bits, keeping leading zeros"""
        self.assertEqual(crc_remainder("0000", "1001"), "000")
        self.assertEqual(crc_remainder("1", "10011"), "0011")

    def test_generator_11_is_parity(self):
        """With G = 11, the CRC bit is the parity bit"""
        for data in ["1", "10", "111", "1011001", "1110000", "0111000110101011"]:
            self.assertEqual(crc_remainder(data, "11"), parity_bit(data), msg=data)

    def test_rejects_bad_input(self):
        """Bad bit strings or generators raise ValueError"""
        for data, gen in [("10a1", "1001"), ("1011", "10x1"), ("1011", "1"), ("1011", "0101"), ("1011", "")]:
            with self.assertRaises(ValueError, msg=f"crc_remainder({data!r}, {gen!r})"):
                crc_remainder(data, gen)


class CrcEncodeAndCheck(unittest.TestCase):
    def test_encode(self):
        """crc_encode appends R to D"""
        self.assertEqual(crc_encode("101110", "1001"), "101110011")

    def test_check_good(self):
        """An undamaged codeword passes"""
        self.assertTrue(crc_check("101110011", "1001"))
        self.assertTrue(crc_check(crc_encode("1101011011", "10011"), "10011"))

    def test_check_flipped_bit(self):
        """The reading's damaged codeword fails"""
        self.assertFalse(crc_check("101010011", "1001"))

    def test_every_single_bit_error_caught(self):
        """Flipping any one bit is always caught"""
        word = crc_encode("11010110110000", "10011")
        for i in range(len(word)):
            flipped = word[:i] + ("1" if word[i] == "0" else "0") + word[i + 1:]
            self.assertFalse(crc_check(flipped, "10011"), msg=f"bit {i} flipped")

    def test_short_bursts_caught(self):
        """Every burst of r or fewer bits is caught (r = 4 here)"""
        word = crc_encode("1001110101110010", "10011")
        n = len(word)
        for length in range(1, 5):
            for start in range(n - length + 1):
                # flip the first and last bit of the burst, and every bit between
                pattern = "1" + "1" * (length - 2) + "1" if length > 1 else "1"
                mask = "0" * start + pattern + "0" * (n - start - length)
                damaged = "".join("1" if a != b else "0" for a, b in zip(word, mask))
                self.assertFalse(crc_check(damaged, "10011"), msg=f"burst of {length} at {start}")


class BuildFrame(unittest.TestCase):
    def test_layout(self):
        """Destination, source, EtherType, payload, FCS"""
        payload = bytes(range(50))
        frame = build_frame(GW, SRC, ETHERTYPE_IPV4, payload)
        self.assertEqual(frame[0:6], bytes.fromhex("3cbdc5407761"))
        self.assertEqual(frame[6:12], bytes.fromhex("3c22fb45a485"))
        self.assertEqual(frame[12:14], b"\x08\x00")
        self.assertEqual(frame[14:64], payload)
        self.assertEqual(len(frame), 14 + 50 + 4)

    def test_fcs(self):
        """The FCS is zlib.crc32 of everything before it, little-endian"""
        frame = build_frame(GW, SRC, ETHERTYPE_IPV6, b"x" * 100)
        self.assertEqual(frame[-4:], zlib.crc32(frame[:-4]).to_bytes(4, "little"))

    def test_ethernet_residue(self):
        """A good Ethernet frame always has the same CRC-32 over the whole thing, FCS included"""
        frame = build_frame(BCAST, SRC, ETHERTYPE_ARP, b"hello")
        self.assertEqual(zlib.crc32(frame), 0x2144DF1C)

    def test_padding(self):
        """A short payload is padded with zeros to 46 bytes: a 64-byte frame"""
        frame = build_frame(BCAST, SRC, ETHERTYPE_ARP, b"who has 192.168.1.1?")
        self.assertEqual(len(frame), 64)
        self.assertEqual(frame[14:34], b"who has 192.168.1.1?")
        self.assertEqual(frame[34:60], bytes(26))

    def test_empty_payload(self):
        """Even no payload makes a 64-byte frame"""
        self.assertEqual(len(build_frame(BCAST, SRC, ETHERTYPE_ARP, b"")), 64)

    def test_largest(self):
        """A 1500-byte payload makes a 1518-byte frame"""
        self.assertEqual(len(build_frame(GW, SRC, ETHERTYPE_IPV4, bytes(1500))), 1518)

    def test_too_big(self):
        """1501 bytes is over the MTU"""
        with self.assertRaises(ValueError):
            build_frame(GW, SRC, ETHERTYPE_IPV4, bytes(1501))


class ParseFrame(unittest.TestCase):
    def test_round_trip(self):
        """parse_frame undoes build_frame"""
        payload = b"A" * 60
        info = parse_frame(build_frame(GW, SRC, ETHERTYPE_IPV4, payload))
        self.assertEqual(info["dst"], GW)
        self.assertEqual(info["src"], SRC)
        self.assertEqual(info["ethertype"], 0x0800)
        self.assertEqual(info["payload"], payload)
        self.assertTrue(info["fcs_ok"])

    def test_padding_stays_in_payload(self):
        """Layer 2 can't tell padding from data, so it stays in the payload"""
        info = parse_frame(build_frame(BCAST, SRC, ETHERTYPE_ARP, b"hi"))
        self.assertEqual(info["payload"], b"hi" + bytes(44))
        self.assertEqual(info["dst"], BCAST)

    def test_corrupted(self):
        """Flip one bit anywhere and the FCS no longer matches"""
        frame = bytearray(build_frame(GW, SRC, ETHERTYPE_IPV4, b"important data" * 5))
        for i in [0, 7, 13, 20, len(frame) - 5, len(frame) - 1]:
            damaged = bytearray(frame)
            damaged[i] ^= 0x10
            self.assertFalse(parse_frame(bytes(damaged))["fcs_ok"], msg=f"byte {i} damaged")

    def test_runt(self):
        """Under 64 bytes is a runt"""
        frame = build_frame(GW, SRC, ETHERTYPE_IPV4, b"")
        with self.assertRaises(ValueError):
            parse_frame(frame[:63])

    def test_too_long(self):
        """Over 1518 bytes isn't a standard frame"""
        with self.assertRaises(ValueError):
            parse_frame(bytes(1519))


if __name__ == "__main__":
    unittest.main()
