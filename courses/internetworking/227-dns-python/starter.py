"""A resolver's toolkit: wire-format names, queries, reverse names, and lookups."""

import struct

# Record and query types, by name, with the number DNS uses on the wire.
QTYPES = {"A": 1, "NS": 2, "CNAME": 5, "SOA": 6, "PTR": 12, "MX": 15, "TXT": 16, "AAAA": 28, "AXFR": 252, "ANY": 255}
MAX_ALIASES = 8


# ---------------------------------------------------------------------------
# Helper, done for you.


def normalize(name):
    """Lowercase, with a trailing dot: "WWW.Example.com" -> "www.example.com."."""
    name = name.lower()
    return name if name.endswith(".") else name + "."


# ---------------------------------------------------------------------------
# Part 1: names and queries on the wire


def encode_name(name):
    """DNS wire format: each label as a length byte then the label, then a 0 byte.

    encode_name("www.example.com") == b"\\x03www\\x07example\\x03com\\x00"
    encode_name(".") == b"\\x00"            (the root has no labels)
    A trailing dot makes no difference. Raise ValueError for a label over 63 bytes.
    """
    # TODO
    pass


def build_query(query_id, name, qtype):
    """A complete query message: 12-byte header + question.

    Header: struct.pack("!HHHHHH", query_id, 0x0100, 1, 0, 0, 0)
            (ID, flags with just rd set, 1 question, 0 answers, 0 authority, 0 additional)
    Question: encode_name(name) + struct.pack("!HH", QTYPES[qtype], 1)
              (QTYPE number, then QCLASS 1 for IN)
    qtype may be given in any case: "mx" or "MX".
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 2: reverse lookups


def reverse_name(ip):
    """"192.0.2.10" -> "10.2.0.192.in-addr.arpa."."""
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 3: step 2 of the resolver algorithm


def closest_zone(name, zones):
    """The zone in `zones` that is the closest ancestor of `name` (or the name itself).

    Compare whole labels from the right: "www.example.com" is inside "example.com"
    and "com" and "." (the root, which contains everything), but "notexample.com"
    is NOT inside "example.com". Ignore case and trailing dots. Return the zone
    exactly as it was given in `zones`, or None if none contains the name.
    """
    # TODO
    pass


# ---------------------------------------------------------------------------
# Part 4: answering from a list of records


def resolve(records, name, rtype):
    """records is a list of (name, type, value) tuples, like a tiny zone.

    Return the values of every record with this name and type, in order.
    If there are none but the name has a CNAME, follow it to its canonical name
    and try again. Return [] if nothing is found, or after MAX_ALIASES (8)
    aliases without an answer (a CNAME loop). Ignore case and trailing dots in
    names, and case in types. Asking for "CNAME" itself returns the CNAME.
    """
    # TODO
    pass


def mail_hosts(records, domain):
    """The domain's MX hosts in the order a sender tries them.

    MX values look like "10 mail1.example.com.". Lowest priority number first;
    hosts with equal priority keep their order from the records.
    """
    # TODO
    pass


if __name__ == "__main__":
    print(encode_name("www.example.com"))          # b'\x03www\x07example\x03com\x00'
    print(reverse_name("198.51.100.7"))            # 7.100.51.198.in-addr.arpa.
    print(closest_zone("www.shop.example.com", [".", "com.", "example.com."]))  # example.com.

    zone = [
        ("example.com.", "MX", "20 mail2.example.com."),
        ("example.com.", "MX", "10 mail1.example.com."),
        ("www.example.com.", "CNAME", "example.com."),
        ("example.com.", "A", "93.184.215.14"),
    ]
    print(resolve(zone, "www.example.com", "A"))   # ['93.184.215.14']
    print(mail_hosts(zone, "example.com"))         # ['mail1.example.com.', 'mail2.example.com.']
