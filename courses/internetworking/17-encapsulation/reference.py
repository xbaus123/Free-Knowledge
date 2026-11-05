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
    return struct.pack("!HHH", src_port, dst_port, len(data)) + data


def transport_unwrap(segment):
    """Return (src_port, dst_port, data). Raise ValueError if malformed."""
    if len(segment) < 6:
        raise ValueError("segment shorter than its header")
    src_port, dst_port, length = struct.unpack("!HHH", segment[:6])
    data = segment[6:]
    if len(data) != length:
        raise ValueError("segment length field doesn't match")
    return src_port, dst_port, data


# --- Layer 3: network --------------------------------------------------------
# | src IP (4) | dst IP (4) | payload length (2) | segment ... |


def network_wrap(segment, src_ip, dst_ip):
    """Return the packet: the network header followed by the segment."""
    return struct.pack("!4s4sH", ip_to_bytes(src_ip), ip_to_bytes(dst_ip), len(segment)) + segment


def network_unwrap(packet):
    """Return (src_ip, dst_ip, segment). Raise ValueError if malformed."""
    if len(packet) < 10:
        raise ValueError("packet shorter than its header")
    src, dst, length = struct.unpack("!4s4sH", packet[:10])
    segment = packet[10:]
    if len(segment) != length:
        raise ValueError("packet length field doesn't match")
    return bytes_to_ip(src), bytes_to_ip(dst), segment


# --- Layer 2: data link ------------------------------------------------------
# | dst MAC (6) | src MAC (6) | payload length (2) | packet ... | FCS (4) |
# FCS = zlib.crc32(header + packet), as a 4-byte number.


def link_wrap(packet, src_mac, dst_mac):
    """Return the frame: header, packet, then the FCS trailer."""
    body = struct.pack("!6s6sH", mac_to_bytes(dst_mac), mac_to_bytes(src_mac), len(packet)) + packet
    return body + struct.pack("!I", zlib.crc32(body))


def link_unwrap(frame):
    """Return (src_mac, dst_mac, packet).

    Raise ValueError if the frame is too short, its length field is wrong,
    or its FCS doesn't match.
    """
    if len(frame) < 18:
        raise ValueError("frame shorter than its header and trailer")
    body, (fcs,) = frame[:-4], struct.unpack("!I", frame[-4:])
    if zlib.crc32(body) != fcs:
        raise ValueError("FCS mismatch: the frame was corrupted")
    dst, src, length = struct.unpack("!6s6sH", body[:14])
    packet = body[14:]
    if len(packet) != length:
        raise ValueError("frame length field doesn't match")
    return bytes_to_mac(src), bytes_to_mac(dst), packet


# --- Layer 1: physical -------------------------------------------------------


def to_bits(frame):
    """b'\\x05' -> '00000101': 8 bits per byte, most significant first."""
    return "".join(f"{b:08b}" for b in frame)


def from_bits(bits):
    """'00000101' -> b'\\x05'. Raise ValueError if it isn't whole bytes of 0s and 1s."""
    if len(bits) % 8 or set(bits) - {"0", "1"}:
        raise ValueError("not a whole number of bytes of 0s and 1s")
    return bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


# --- The whole stack ---------------------------------------------------------


def send(data, src, dst):
    """Encapsulate data all the way down to bits.

    src and dst look like {"mac": "aa:bb:cc:00:11:22", "ip": "10.0.0.1", "port": 5000}.
    """
    segment = transport_wrap(data, src["port"], dst["port"])
    packet = network_wrap(segment, src["ip"], dst["ip"])
    frame = link_wrap(packet, src["mac"], dst["mac"])
    return to_bits(frame)


def receive(bits):
    """De-encapsulate bits all the way up.

    Return {"data": ..., "src": {"mac", "ip", "port"}, "dst": {"mac", "ip", "port"}}.
    """
    src_mac, dst_mac, packet = link_unwrap(from_bits(bits))
    src_ip, dst_ip, segment = network_unwrap(packet)
    src_port, dst_port, data = transport_unwrap(segment)
    return {
        "data": data,
        "src": {"mac": src_mac, "ip": src_ip, "port": src_port},
        "dst": {"mac": dst_mac, "ip": dst_ip, "port": dst_port},
    }


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
