import random
import unittest

import solution
from solution import Receiver, Resolver


def a(ip, ttl):
    return {"type": "A", "value": ip, "ttl": ttl}


def cname(target, ttl):
    return {"type": "CNAME", "value": target, "ttl": ttl}


def ns(server, ttl):
    return {"type": "NS", "value": server, "ttl": ttl}


# Each server's records. An NS record delegates every name in its zone.
ZONES = {
    "root": {"com": ns("tld-com", 172800), "net": ns("tld-net", 172800)},
    "tld-com": {"example.com": ns("ns1.example", 86400), "shop.com": ns("ns.shop", 86400)},
    "tld-net": {"fastcdn.net": ns("ns.fastcdn", 3600)},
    "ns1.example": {
        "example.com": a("93.184.216.34", 300),
        "www.example.com": a("93.184.216.34", 300),
        "mail.example.com": a("93.184.216.40", 300),
        "api.example.com": cname("edge.fastcdn.net", 600),
    },
    "ns.shop": {"shop.com": a("203.0.113.7", 60)},
    "ns.fastcdn": {"edge.fastcdn.net": a("151.101.1.1", 30)},
}


class FakeNetwork:
    def __init__(self):
        self.queries = []

    def query(self, server, name):
        self.queries.append((server, name))
        records = ZONES[server]
        if name in records and records[name]["type"] != "NS":
            return dict(records[name])
        for zone, rec in records.items():
            if rec["type"] == "NS" and (name == zone or name.endswith("." + zone)):
                return dict(rec, zone=zone)
        return None

    def take(self):
        q, self.queries = self.queries, []
        return q


class IPTest(unittest.TestCase):
    def test_ip_to_int(self):
        """converts dotted IPv4 addresses to 32-bit numbers"""
        self.assertEqual(solution.ip_to_int("0.0.0.0"), 0)
        self.assertEqual(solution.ip_to_int("0.0.1.0"), 256)
        self.assertEqual(solution.ip_to_int("192.168.1.10"), 3232235786)
        self.assertEqual(solution.ip_to_int("255.255.255.255"), 2**32 - 1)

    def test_rejects_bad_addresses(self):
        """rejects anything that isn't four numbers from 0 to 255"""
        for bad in ("256.1.1.1", "1.2.3", "1.2.3.4.5", "a.b.c.d", "1.2.3.-4", "", "1..2.3"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                solution.ip_to_int(bad)

    def test_in_subnet(self):
        """checks CIDR blocks by comparing the leading bits"""
        cases = [
            ("10.1.2.3", "10.0.0.0/8", True),
            ("11.1.2.3", "10.0.0.0/8", False),
            ("192.168.1.77", "192.168.1.0/24", True),
            ("192.168.2.77", "192.168.1.0/24", False),
            ("172.31.255.255", "172.16.0.0/12", True),
            ("172.32.0.0", "172.16.0.0/12", False),
            ("8.8.8.8", "0.0.0.0/0", True),
            ("8.8.8.8", "8.8.8.8/32", True),
            ("8.8.8.9", "8.8.8.8/32", False),
        ]
        for address, cidr, want in cases:
            self.assertEqual(solution.in_subnet(address, cidr), want, f"{address} in {cidr}")


class ReceiverTest(unittest.TestCase):
    def test_in_order(self):
        """delivers in-order segments and acknowledges the next byte"""
        r = Receiver()
        self.assertEqual(r.receive(0, b"GET / "), 6)
        self.assertEqual(r.receive(6, b"HTTP/1.1"), 14)
        self.assertEqual(r.data, b"GET / HTTP/1.1")

    def test_out_of_order(self):
        """holds early segments until the gap before them is filled"""
        r = Receiver()
        self.assertEqual(r.receive(5, b"world"), 0, "byte 0 is still missing")
        self.assertEqual(r.data, b"", "nothing can be delivered past a gap")
        self.assertEqual(r.receive(10, b"!"), 0)
        self.assertEqual(r.receive(0, b"hello"), 11)
        self.assertEqual(r.data, b"helloworld!")

    def test_duplicates_and_overlaps(self):
        """ignores bytes it already has, including overlapping retransmissions"""
        r = Receiver()
        r.receive(0, b"abc")
        self.assertEqual(r.receive(0, b"abc"), 3)
        self.assertEqual(r.receive(1, b"bcdef"), 6, "a retransmission can overlap what you have")
        self.assertEqual(r.receive(2, b"cd"), 6)
        self.assertEqual(r.data, b"abcdef")

    def test_scrambled_stream(self):
        """reassembles a stream that arrives shuffled, with duplicates"""
        message = bytes(range(256)) * 8
        segments = [(i, message[i : i + 37]) for i in range(0, len(message), 37)]
        rng = random.Random(7)
        arrivals = segments + rng.sample(segments, 20)
        rng.shuffle(arrivals)
        r = Receiver()
        acks = [r.receive(seq, payload) for seq, payload in arrivals]
        self.assertEqual(r.data, message)
        self.assertEqual(acks, sorted(acks), "the cumulative ACK never goes backward")
        self.assertEqual(acks[-1], len(message))


class ResolverTest(unittest.TestCase):
    def setUp(self):
        self.net = FakeNetwork()
        self.dns = Resolver(self.net)

    def test_walks_the_hierarchy(self):
        """walks from the root to the authoritative server"""
        self.assertEqual(self.dns.resolve("www.example.com", 0), "93.184.216.34")
        self.assertEqual(
            self.net.take(),
            [("root", "www.example.com"), ("tld-com", "www.example.com"), ("ns1.example", "www.example.com")],
        )

    def test_caches_answers_until_ttl(self):
        """answers from the cache until the record's TTL expires"""
        self.dns.resolve("www.example.com", 0)
        self.net.take()
        self.assertEqual(self.dns.resolve("www.example.com", 299), "93.184.216.34")
        self.assertEqual(self.net.take(), [], "a cached answer needs no queries")
        self.assertEqual(self.dns.resolve("www.example.com", 300), "93.184.216.34")
        self.assertEqual(
            self.net.take(),
            [("ns1.example", "www.example.com")],
            "at its TTL the answer expires, but the referral to ns1.example is still cached",
        )

    def test_caches_referrals(self):
        """starts at the closest cached zone"""
        self.dns.resolve("www.example.com", 0)
        self.net.take()
        self.assertEqual(self.dns.resolve("mail.example.com", 10), "93.184.216.40")
        self.assertEqual(self.net.take(), [("ns1.example", "mail.example.com")])
        self.assertEqual(self.dns.resolve("example.com", 10), "93.184.216.34")
        self.assertEqual(self.net.take(), [("ns1.example", "example.com")], "a zone contains its own name")
        self.assertEqual(self.dns.resolve("shop.com", 10), "203.0.113.7")
        self.assertEqual(self.net.take(), [("tld-com", "shop.com"), ("ns.shop", "shop.com")])
        self.dns.resolve("www.example.com", 86400 + 1)
        self.assertEqual(
            self.net.take(),
            [("tld-com", "www.example.com"), ("ns1.example", "www.example.com")],
            "once example.com's referral expires, start from the com servers",
        )

    def test_follows_cnames(self):
        """follows a CNAME to another zone and caches both records"""
        self.assertEqual(self.dns.resolve("api.example.com", 0), "151.101.1.1")
        self.assertEqual(
            self.net.take(),
            [
                ("root", "api.example.com"),
                ("tld-com", "api.example.com"),
                ("ns1.example", "api.example.com"),
                ("root", "edge.fastcdn.net"),
                ("tld-net", "edge.fastcdn.net"),
                ("ns.fastcdn", "edge.fastcdn.net"),
            ],
        )
        self.assertEqual(self.dns.resolve("api.example.com", 100), "151.101.1.1")
        self.assertEqual(
            self.net.take(),
            [("ns.fastcdn", "edge.fastcdn.net")],
            "the alias is cached for 600s, but the CDN's 30s A record has expired",
        )

    def test_missing_names(self):
        """returns None for names that don't exist"""
        self.assertIsNone(self.dns.resolve("nope.example.com", 0))
        self.assertIsNone(self.dns.resolve("example.org", 0))


class LatencyTest(unittest.TestCase):
    def test_transfer_time(self):
        """adds handshake round trips and transmission time"""
        # 1 MB at 100 Mbit/s takes 80 ms to transmit.
        self.assertAlmostEqual(solution.transfer_ms(1_000_000, 100, 80, new_connection=True, tls=True), 320)
        self.assertAlmostEqual(solution.transfer_ms(1_000_000, 100, 80, new_connection=True), 240)
        self.assertAlmostEqual(solution.transfer_ms(1_000_000, 100, 80, new_connection=False, tls=True), 160)

    def test_latency_dominates_small_requests(self):
        """a small request costs round trips, not bandwidth"""
        slow_link = solution.transfer_ms(2_000, 10, 2, new_connection=False)
        far_away = solution.transfer_ms(2_000, 10_000, 150, new_connection=False)
        self.assertAlmostEqual(slow_link, 3.6)
        self.assertAlmostEqual(far_away, 150.0016)

    def test_window_limits_throughput(self):
        """a window limits throughput to window / RTT"""
        self.assertAlmostEqual(solution.max_throughput_mbps(65_536, 100), 5.24288)
        self.assertAlmostEqual(solution.max_throughput_mbps(65_536, 1), 524.288)

    def test_bandwidth_delay_product(self):
        """bandwidth × RTT is how much data fills the pipe"""
        self.assertAlmostEqual(solution.bandwidth_delay_product(1_000, 100), 12_500_000)
        self.assertAlmostEqual(solution.bandwidth_delay_product(100, 20), 250_000)
        window = solution.bandwidth_delay_product(1_000, 100)
        self.assertAlmostEqual(solution.max_throughput_mbps(window, 100), 1_000)


if __name__ == "__main__":
    unittest.main()
