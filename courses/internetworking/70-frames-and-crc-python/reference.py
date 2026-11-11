"""Error detection and Ethernet frames: parity, CRC by hand, and a real FCS."""

import zlib

ETHERTYPE_IPV4 = 0x0800
ETHERTYPE_ARP = 0x0806
ETHERTYPE_IPV6 = 0x86DD


def _check_bits(bits):
    if not isinstance(bits, str) or any(b not in "01" for b in bits):
        raise ValueError(f"not a bit string: {bits!r}")


def parity_bit(bits):
    _check_bits(bits)
    return "1" if bits.count("1") % 2 else "0"


def crc_remainder(data, generator):
    _check_bits(data)
    _check_bits(generator)
    if len(generator) < 2 or generator[0] != "1":
        raise ValueError("generator must be at least 2 bits and start with 1")
    r = len(generator) - 1
    bits = [int(b) for b in data + "0" * r]
    g = [int(b) for b in generator]
    for i in range(len(data)):
        if bits[i]:
            for j in range(len(g)):
                bits[i + j] ^= g[j]
    return "".join(str(b) for b in bits[-r:])


def crc_encode(data, generator):
    return data + crc_remainder(data, generator)


def crc_check(codeword, generator):
    _check_bits(codeword)
    r = len(generator) - 1
    if len(codeword) <= r:
        return False
    return crc_remainder(codeword, generator) == "0" * r


def _mac_bytes(mac):
    raw = bytes.fromhex(mac.replace(":", ""))
    if len(raw) != 6:
        raise ValueError(f"not a MAC address: {mac!r}")
    return raw


def _mac_text(raw):
    return ":".join(f"{b:02x}" for b in raw)


def build_frame(dst, src, ethertype, payload):
    if len(payload) > 1500:
        raise ValueError("payload is larger than the 1500-byte MTU")
    payload = payload + bytes(max(0, 46 - len(payload)))
    body = _mac_bytes(dst) + _mac_bytes(src) + ethertype.to_bytes(2, "big") + payload
    return body + zlib.crc32(body).to_bytes(4, "little")


def parse_frame(frame):
    if len(frame) < 64:
        raise ValueError("runt: shorter than 64 bytes")
    if len(frame) > 1518:
        raise ValueError("larger than 1518 bytes")
    body, fcs = frame[:-4], frame[-4:]
    return {
        "dst": _mac_text(frame[0:6]),
        "src": _mac_text(frame[6:12]),
        "ethertype": int.from_bytes(frame[12:14], "big"),
        "payload": frame[14:-4],
        "fcs_ok": zlib.crc32(body).to_bytes(4, "little") == fcs,
    }
