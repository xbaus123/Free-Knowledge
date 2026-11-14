import struct
import unittest

from solution import build_query, closest_zone, encode_name, mail_hosts, resolve, reverse_name

ZONE = [
    ("example.com.", "SOA", "ns1.example.com. admin.example.com. 2026111301 3600 1200 259200 3600"),
    ("example.com.", "NS", "ns1.example.com."),
    ("example.com.", "NS", "ns2.example.com."),
    ("example.com.", "A", "93.184.215.14"),
    ("example.com.", "MX", "20 mail2.example.com."),
    ("example.com.", "MX", "10 mail1.example.com."),
    ("example.com.", "MX", "20 mail3.example.com."),
    ("www.example.com.", "CNAME", "example.com."),
    ("shop.example.com.", "CNAME", "www.example.com."),
    ("mail1.example.com.", "A", "192.0.2.10"),
    ("mail1.example.com.", "A", "192.0.2.11"),
    ("v6.example.com.", "AAAA", "2001:db8::5"),
    ("loop1.example.com.", "CNAME", "loop2.example.com."),
    ("loop2.example.com.", "CNAME", "loop1.example.com."),
    ("10.2.0.192.in-addr.arpa.", "PTR", "mail1.example.com."),
]


class EncodeName(unittest.TestCase):
    def test_reading_example(self):
        """www.example.com, as in the reading"""
        self.assertEqual(encode_name("www.example.com"), b"\x03www\x07example\x03com\x00")

    def test_trailing_dot(self):
        """A trailing dot makes no difference"""
        self.assertEqual(encode_name("www.example.com."), encode_name("www.example.com"))

    def test_root(self):
        """The root is just the zero byte"""
        self.assertEqual(encode_name("."), b"\x00")

    def test_one_label(self):
        """A TLD on its own"""
        self.assertEqual(encode_name("edu"), b"\x03edu\x00")

    def test_label_too_long(self):
        """63 bytes is the limit for one label"""
        self.assertEqual(len(encode_name("a" * 63 + ".com")), 1 + 63 + 1 + 3 + 1)
        with self.assertRaises(ValueError):
            encode_name("a" * 64 + ".com")


class BuildQuery(unittest.TestCase):
    def test_header(self):
        """ID, rd flag, one question, nothing else"""
        msg = build_query(0x1234, "marshall.edu", "MX")
        self.assertEqual(msg[:12], struct.pack("!HHHHHH", 0x1234, 0x0100, 1, 0, 0, 0))

    def test_question(self):
        """Encoded name, then QTYPE and QCLASS"""
        msg = build_query(1, "marshall.edu", "MX")
        self.assertEqual(msg[12:], b"\x08marshall\x03edu\x00" + struct.pack("!HH", 15, 1))

    def test_whole_message(self):
        """An A query for example.com, byte for byte"""
        expected = bytes.fromhex("abcd01000001000000000000") + b"\x07example\x03com\x00\x00\x01\x00\x01"
        self.assertEqual(build_query(0xABCD, "example.com", "A"), expected)

    def test_types(self):
        """Lowercase types work, and AXFR is 252"""
        self.assertEqual(build_query(7, "example.com", "soa")[-4:], struct.pack("!HH", 6, 1))
        self.assertEqual(build_query(7, "example.com", "AXFR")[-4:], struct.pack("!HH", 252, 1))


class ReverseName(unittest.TestCase):
    def test_reading_example(self):
        """192.0.2.10, as in the MX and PTR reading"""
        self.assertEqual(reverse_name("192.0.2.10"), "10.2.0.192.in-addr.arpa.")

    def test_check_example(self):
        """198.51.100.7, from the check quiz"""
        self.assertEqual(reverse_name("198.51.100.7"), "7.100.51.198.in-addr.arpa.")

    def test_marshall_mail(self):
        """One of marshall.edu's mail addresses"""
        self.assertEqual(reverse_name("52.101.42.14"), "14.42.101.52.in-addr.arpa.")


class ClosestZone(unittest.TestCase):
    ZONES = [".", "com.", "example.com.", "net."]

    def test_closest_ancestor(self):
        """The deepest zone above the name wins"""
        self.assertEqual(closest_zone("www.shop.example.com", self.ZONES), "example.com.")

    def test_order_does_not_matter(self):
        """Like longest prefix match, the order of the list doesn't matter"""
        self.assertEqual(closest_zone("www.example.com", list(reversed(self.ZONES))), "example.com.")

    def test_falls_back_to_tld_and_root(self):
        """The drill: cdn.example.net only has the root and net above it"""
        self.assertEqual(closest_zone("cdn.example.net", self.ZONES), "net.")
        self.assertEqual(closest_zone("marshall.edu", self.ZONES), ".")

    def test_whole_labels_only(self):
        """notexample.com is not inside example.com"""
        self.assertEqual(closest_zone("notexample.com", self.ZONES), "com.")

    def test_the_zone_itself(self):
        """A zone is its own closest zone"""
        self.assertEqual(closest_zone("example.com", self.ZONES), "example.com.")

    def test_case_and_dots(self):
        """Ignore case and trailing dots, and return the zone as given"""
        self.assertEqual(closest_zone("WWW.Example.COM.", ["com", "Example.com"]), "Example.com")

    def test_none(self):
        """No zone above the name"""
        self.assertIsNone(closest_zone("marshall.edu", ["com.", "example.com."]))


class Resolve(unittest.TestCase):
    def test_direct(self):
        """A plain A lookup"""
        self.assertEqual(resolve(ZONE, "example.com", "A"), ["93.184.215.14"])

    def test_many_addresses(self):
        """Several A records come back together, in order"""
        self.assertEqual(resolve(ZONE, "mail1.example.com", "A"), ["192.0.2.10", "192.0.2.11"])

    def test_follow_cname(self):
        """www is an alias for example.com"""
        self.assertEqual(resolve(ZONE, "www.example.com", "A"), ["93.184.215.14"])

    def test_cname_chain(self):
        """shop -> www -> example.com"""
        self.assertEqual(resolve(ZONE, "shop.example.com", "A"), ["93.184.215.14"])

    def test_ask_for_the_cname(self):
        """Asking for the CNAME itself returns it"""
        self.assertEqual(resolve(ZONE, "shop.example.com", "CNAME"), ["www.example.com."])

    def test_case_and_dots(self):
        """Names ignore case and trailing dots, types ignore case"""
        self.assertEqual(resolve(ZONE, "WWW.EXAMPLE.COM.", "a"), ["93.184.215.14"])

    def test_no_data(self):
        """The name exists but has no record of that type (NOERROR, ANSWER: 0)"""
        self.assertEqual(resolve(ZONE, "v6.example.com", "A"), [])
        self.assertEqual(resolve(ZONE, "v6.example.com", "AAAA"), ["2001:db8::5"])

    def test_no_name(self):
        """The name doesn't exist (NXDOMAIN)"""
        self.assertEqual(resolve(ZONE, "nope.example.com", "A"), [])

    def test_cname_loop(self):
        """A CNAME loop gives up instead of hanging"""
        self.assertEqual(resolve(ZONE, "loop1.example.com", "A"), [])

    def test_reverse(self):
        """A PTR lookup using your reverse_name"""
        self.assertEqual(resolve(ZONE, reverse_name("192.0.2.10"), "PTR"), ["mail1.example.com."])


class MailHosts(unittest.TestCase):
    def test_priority_order(self):
        """Lowest number first; equal priorities keep their order"""
        self.assertEqual(mail_hosts(ZONE, "example.com"),
                         ["mail1.example.com.", "mail2.example.com.", "mail3.example.com."])

    def test_marshall(self):
        """marshall.edu's single MX at priority 0"""
        zone = [("marshall.edu.", "MX", "0 marshall-edu.mail.protection.outlook.com.")]
        self.assertEqual(mail_hosts(zone, "marshall.edu"), ["marshall-edu.mail.protection.outlook.com."])

    def test_no_mx(self):
        """whitehouse.gov: no MX records at all"""
        zone = [("whitehouse.gov.", "SOA", "ernest.ns.cloudflare.com. dns.cloudflare.com. 2351553162 10000 2400 604800 1800")]
        self.assertEqual(mail_hosts(zone, "whitehouse.gov"), [])

    def test_numeric_sort(self):
        """Priorities compare as numbers: 5 comes before 10"""
        zone = [("x.org.", "MX", "10 b.x.org."), ("x.org.", "MX", "5 a.x.org.")]
        self.assertEqual(mail_hosts(zone, "x.org"), ["a.x.org.", "b.x.org."])


if __name__ == "__main__":
    unittest.main()
