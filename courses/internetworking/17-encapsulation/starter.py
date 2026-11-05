"""Encapsulation: build a tiny network stack, one layer at a time.

Going down, each layer wraps what it gets in its own header (the data
link layer adds a trailer too). Coming up, each layer checks and strips
its own header and hands the rest to the layer above.
"""

import struct
import zlib


# --- Helpers (already done) -------------------------------------------------


def ip_to_bytes(ip):
    """'10.0.0.1' -> b'\\x0a\\x00\\x00\\x01'"""
    return bytes(int(part) for part in ip.split("."))


def bytes_to_ip(raw):
    """b'\\x0a\\x00\\x00\\x01' -> '10.0.0.1'"""
    return ".".join(str(b) for b in raw)


def mac_to_bytes(mac):
    """'aa:bb:cc:00:11:22' -> 6 bytes"""
    return bytes(int(part, 16) for part in mac.split(":"))


def bytes_to_mac(raw):
    """6 bytes -> 'aa:bb:cc:00:11:22'"""
    return ":".join(f"{b:02x}" for b in raw)


# --- Layer 4: transport ------------------------------------------------------
# | src port (2) | dst port (2) | data length (2) | data ... |


def transport_wrap(data, src_port, dst_port):
    """Return the segment: the transport header followed by data."""
    raise NotImplementedError


def transport_unwrap(segment):
    """Return (src_port, dst_port, data). Raise ValueError if malformed."""
    raise NotImplementedError


# --- Layer 3: network --------------------------------------------------------
# | src IP (4) | dst IP (4) | payload length (2) | segment ... |


def network_wrap(segment, src_ip, dst_ip):
    """Return the packet: the network header followed by the segment."""
    raise NotImplementedError


def network_unwrap(packet):
    """Return (src_ip, dst_ip, segment). Raise ValueError if malformed."""
    raise NotImplementedError


# --- Layer 2: data link ------------------------------------------------------
# | dst MAC (6) | src MAC (6) | payload length (2) | packet ... | FCS (4) |
# FCS = zlib.crc32(header + packet), as a 4-byte number.


def link_wrap(packet, src_mac, dst_mac):
    """Return the frame: header, packet, then the FCS trailer."""
    raise NotImplementedError


def link_unwrap(frame):
    """Return (src_mac, dst_mac, packet).

    Raise ValueError if the frame is too short, its length field is wrong,
    or its FCS doesn't match.
    """
    raise NotImplementedError


# --- Layer 1: physical -------------------------------------------------------


def to_bits(frame):
    """b'\\x05' -> '00000101': 8 bits per byte, most significant first."""
    raise NotImplementedError


def from_bits(bits):
    """'00000101' -> b'\\x05'. Raise ValueError if it isn't whole bytes of 0s and 1s."""
    raise NotImplementedError


# --- The whole stack ---------------------------------------------------------


def send(data, src, dst):
    """Encapsulate data all the way down to bits.

    src and dst look like {"mac": "aa:bb:cc:00:11:22", "ip": "10.0.0.1", "port": 5000}.
    """
    raise NotImplementedError


def receive(bits):
    """De-encapsulate bits all the way up.

    Return {"data": ..., "src": {"mac", "ip", "port"}, "dst": {"mac", "ip", "port"}}.
    """
    raise NotImplementedError


if __name__ == "__main__":
    alice = {"mac": "aa:aa:aa:00:00:01", "ip": "10.0.0.1", "port": 5000}
    bob = {"mac": "bb:bb:bb:00:00:02", "ip": "10.0.0.2", "port": 80}
    segment = transport_wrap(b"hello", alice["port"], bob["port"])
    print("segment:", segment.hex(" "))
    packet = network_wrap(segment, alice["ip"], bob["ip"])
    print("packet: ", packet.hex(" "))
    frame = link_wrap(packet, alice["mac"], bob["mac"])
    print("frame:  ", frame.hex(" "))
    print("bits:   ", to_bits(frame)[:64], "...")
    print("received:", receive(send(b"hello", alice, bob)))
