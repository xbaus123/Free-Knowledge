"""MAC addresses: parse them, take them apart, and say what they are."""

# OUIs from the arp -a examples, and a couple more.
VENDORS = {
    "3c:bd:c5": "Arcadyan",
    "3c:22:fb": "Apple",
    "dc:46:28": "Intel",
    "4c:77:cb": "Intel",
    "00:00:5e": "IANA",
    "00:1b:63": "Apple",
}

HEX = set("0123456789abcdef")


def normalize_mac(text):
    """Return text as six two-digit lowercase hex pairs joined by colons."""
    s = text.strip().lower()
    if "." in s:
        groups = s.split(".")
        if len(groups) != 3 or any(len(g) != 4 for g in groups):
            raise ValueError(f"not a MAC address: {text!r}")
        s = "".join(groups)
        octets = [s[i:i + 2] for i in range(0, 12, 2)]
    elif ":" in s or "-" in s:
        octets = s.replace("-", ":").split(":")
        if len(octets) != 6 or any(not 1 <= len(o) <= 2 for o in octets):
            raise ValueError(f"not a MAC address: {text!r}")
        octets = [o.zfill(2) for o in octets]
    else:
        if len(s) != 12:
            raise ValueError(f"not a MAC address: {text!r}")
        octets = [s[i:i + 2] for i in range(0, 12, 2)]
    if any(not set(o) <= HEX for o in octets):
        raise ValueError(f"not a MAC address: {text!r}")
    return ":".join(octets)


def first_byte(mac):
    return int(normalize_mac(mac)[:2], 16)


def oui(mac):
    """The first three octets, normalized: '3c:bd:c5'."""
    return normalize_mac(mac)[:8]


def is_broadcast(mac):
    return normalize_mac(mac) == "ff:ff:ff:ff:ff:ff"


def is_multicast(mac):
    """The I/G bit: bit 0 of the first byte."""
    return first_byte(mac) & 1 == 1


def is_locally_administered(mac):
    """The U/L bit: bit 1 of the first byte."""
    return first_byte(mac) & 2 == 2


def describe(mac, vendors=VENDORS):
    if is_broadcast(mac):
        return "broadcast"
    if is_multicast(mac):
        return "multicast"
    if is_locally_administered(mac):
        return "locally administered"
    return vendors.get(oui(mac), "unknown")
