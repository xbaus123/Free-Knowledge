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


def normalize_mac(text):
    """Return text as six two-digit lowercase hex pairs joined by colons.

    Accept all of these, and return "01:00:5e:00:00:fb" for each:
        "01:00:5e:00:00:fb"   colons (macOS, Linux)
        "01-00-5E-00-00-FB"   dashes and capitals (Windows)
        "0100.5e00.00fb"      three dotted groups of four (Cisco)
        "01005e0000fb"        twelve bare hex digits
        "1:0:5e:0:0:fb"       leading zeros dropped (macOS arp -a)
    Ignore spaces around the address. Raise ValueError for anything else:
    the wrong number of octets, an octet longer than two digits, or a
    character that isn't hex.
    """
    # TODO
    pass


def oui(mac):
    """The first three octets, normalized: oui("3C-BD-C5-40-77-61") == "3c:bd:c5"."""
    # TODO
    pass


def is_broadcast(mac):
    """True for ff:ff:ff:ff:ff:ff, in any format."""
    # TODO
    pass


def is_multicast(mac):
    """True if bit 0 of the first byte (the I/G bit) is 1.

    Broadcast counts as multicast too: it's the group containing everyone.
    """
    # TODO
    pass


def is_locally_administered(mac):
    """True if bit 1 of the first byte (the U/L bit) is 1."""
    # TODO
    pass


def describe(mac, vendors=VENDORS):
    """Say what kind of address this is. Check in this order:

    "broadcast", then "multicast", then "locally administered";
    otherwise the vendor for its OUI from `vendors`, or "unknown".
    """
    # TODO
    pass


if __name__ == "__main__":
    for line in ["3c:bd:c5:40:77:61", "da:47:5e:b3:f2:81", "1:0:5e:0:0:fb", "ff:ff:ff:ff:ff:ff"]:
        print(line, "->", describe(line))
