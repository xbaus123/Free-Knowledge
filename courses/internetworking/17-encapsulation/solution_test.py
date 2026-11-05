import struct
import unittest
import zlib

from solution import (
    from_bits,
    link_unwrap,
    link_wrap,
    network_unwrap,
    network_wrap,
    receive,
    send,
    to_bits,
    transport_unwrap,
    transport_wrap,
)

ALICE = {"mac": "aa:aa:aa:00:00:01", "ip": "10.0.0.1", "port": 5000}
BOB = {"mac": "bb:bb:bb:00:00:02", "ip": "192.168.1.20", "port": 80}


class Transport(unittest.TestCase):
    def test_header_layout(self):
        """Transport header: src port, dst port, data length, then the data"""
        self.assertEqual(
            transport_wrap(b"hello", 5000, 80),
            bytes.fromhex("1388 0050 0005") + b"hello",
        )

    def test_round_trip(self):
        """transport_unwrap undoes transport_wrap"""
        self.assertEqual(transport_unwrap(transport_wrap(b"GET /", 49152, 443)), (49152, 443, b"GET /"))

    def test_empty_data(self):
        """A segment can carry no data at all"""
        self.assertEqual(transport_unwrap(transport_wrap(b"", 1, 2)), (1, 2, b""))

    def test_rejects_short_segment(self):
        """A segment shorter than its 6-byte header raises ValueError"""
        with self.assertRaises(ValueError):
            transport_unwrap(b"\x13\x88\x00")

    def test_rejects_wrong_length(self):
        """A segment whose length field doesn't match raises ValueError"""
        with self.assertRaises(ValueError):
            transport_unwrap(bytes.fromhex("1388 0050 0009") + b"hello")


class Network(unittest.TestCase):
    def test_header_layout(self):
        """Network header: src IP, dst IP, payload length, then the segment"""
        self.assertEqual(
            network_wrap(b"seg", "10.0.0.1", "192.168.1.20"),
            bytes.fromhex("0a000001 c0a80114 0003") + b"seg",
        )

    def test_round_trip(self):
        """network_unwrap undoes network_wrap"""
        self.assertEqual(
            network_unwrap(network_wrap(b"abc", "172.16.5.4", "8.8.8.8")),
            ("172.16.5.4", "8.8.8.8", b"abc"),
        )

    def test_payload_is_opaque(self):
        """The network layer carries any bytes without looking inside them"""
        weird = bytes(range(256))
        self.assertEqual(network_unwrap(network_wrap(weird, "1.2.3.4", "5.6.7.8"))[2], weird)

    def test_rejects_short_packet(self):
        """A packet shorter than its 10-byte header raises ValueError"""
        with self.assertRaises(ValueError):
            network_unwrap(bytes.fromhex("0a000001 c0a8"))

    def test_rejects_wrong_length(self):
        """A packet whose length field doesn't match raises ValueError"""
        with self.assertRaises(ValueError):
            network_unwrap(bytes.fromhex("0a000001 c0a80114 0002") + b"seg")


class DataLink(unittest.TestCase):
    def test_frame_layout(self):
        """Frame: dst MAC first, then src MAC, length, packet, and a CRC-32 FCS"""
        frame = link_wrap(b"pkt", "aa:aa:aa:00:00:01", "bb:bb:bb:00:00:02")
        body = bytes.fromhex("bbbbbb000002 aaaaaa000001 0003") + b"pkt"
        self.assertEqual(frame, body + struct.pack("!I", zlib.crc32(body)))

    def test_round_trip(self):
        """link_unwrap undoes link_wrap"""
        frame = link_wrap(b"payload", ALICE["mac"], BOB["mac"])
        self.assertEqual(link_unwrap(frame), (ALICE["mac"], BOB["mac"], b"payload"))

    def test_detects_flipped_bit(self):
        """Flipping any single bit makes link_unwrap raise ValueError"""
        frame = link_wrap(b"important", ALICE["mac"], BOB["mac"])
        for i in range(len(frame)):
            for bit in (0, 7):
                damaged = bytearray(frame)
                damaged[i] ^= 1 << bit
                with self.assertRaises(ValueError, msg=f"byte {i}, bit {bit}"):
                    link_unwrap(bytes(damaged))

    def test_rejects_short_frame(self):
        """A frame shorter than its header and trailer raises ValueError"""
        with self.assertRaises(ValueError):
            link_unwrap(b"\x00" * 10)

    def test_rejects_wrong_length_with_valid_fcs(self):
        """A frame with a correct FCS but a wrong length field still raises ValueError"""
        body = bytes.fromhex("bbbbbb000002 aaaaaa000001 0007") + b"pkt"
        with self.assertRaises(ValueError):
            link_unwrap(body + struct.pack("!I", zlib.crc32(body)))


class Physical(unittest.TestCase):
    def test_to_bits(self):
        """to_bits writes 8 bits per byte, most significant bit first"""
        self.assertEqual(to_bits(b"\x05\xa0"), "0000010110100000")

    def test_round_trip(self):
        """from_bits undoes to_bits"""
        data = bytes(range(0, 256, 7))
        self.assertEqual(from_bits(to_bits(data)), data)

    def test_rejects_partial_byte(self):
        """from_bits raises ValueError when the bits aren't whole bytes"""
        with self.assertRaises(ValueError):
            from_bits("0101")

    def test_rejects_other_characters(self):
        """from_bits raises ValueError for anything but 0 and 1"""
        with self.assertRaises(ValueError):
            from_bits("0000201x")


class WholeStack(unittest.TestCase):
    def test_send_nests_every_layer(self):
        """send() wraps transport inside network inside link, then converts to bits"""
        segment = transport_wrap(b"hi", ALICE["port"], BOB["port"])
        packet = network_wrap(segment, ALICE["ip"], BOB["ip"])
        frame = link_wrap(packet, ALICE["mac"], BOB["mac"])
        self.assertEqual(send(b"hi", ALICE, BOB), to_bits(frame))

    def test_receive_round_trip(self):
        """receive(send(...)) gives back the data and both endpoints' addresses"""
        got = receive(send(b"GET /index.html", ALICE, BOB))
        self.assertEqual(got, {"data": b"GET /index.html", "src": ALICE, "dst": BOB})

    def test_receive_rejects_noise(self):
        """A bit flipped on the wire is caught on the way up"""
        bits = list(send(b"transfer $100", ALICE, BOB))
        i = len(bits) // 2
        bits[i] = "1" if bits[i] == "0" else "0"
        with self.assertRaises(ValueError):
            receive("".join(bits))


if __name__ == "__main__":
    unittest.main()
