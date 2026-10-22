import itertools
import random
import unittest

from solution import GlobalRouter, NoRegion, PNCounter, cache_key, edge_ttl

REGIONS = {
    "us-east": {"location": (39.0, -77.5), "jurisdiction": "US", "capacity": 2},
    "us-west": {"location": (45.6, -121.2), "jurisdiction": "US", "capacity": 100},
    "eu-west": {"location": (53.3, -6.3), "jurisdiction": "EU", "capacity": 100},
    "eu-central": {"location": (50.1, 8.7), "jurisdiction": "EU", "capacity": 100},
    "ap-south": {"location": (19.1, 72.9), "jurisdiction": "IN", "capacity": 100},
    "ap-northeast": {"location": (35.7, 139.7), "jurisdiction": "JP", "capacity": 100},
}
RESIDENCY = {"EU": {"EU"}, "IN": {"IN"}}

NEW_YORK = (40.7, -74.0)
PARIS = (48.9, 2.35)
LONDON = (51.5, -0.13)
BOSTON = (42.4, -71.1)
MUMBAI = (19.1, 72.9)
TOKYO = (35.7, 139.7)
SINGAPORE = (1.35, 103.8)


def router():
    return GlobalRouter(REGIONS, RESIDENCY)


class RoutingTest(unittest.TestCase):
    def test_nearest(self):
        """sends users to the nearest region"""
        r = router()
        self.assertEqual(r.route(NEW_YORK, "US"), "us-east")
        self.assertEqual(r.route(PARIS, "EU"), "eu-central")
        self.assertEqual(r.route(LONDON, "UK"), "eu-west")
        self.assertEqual(r.route(TOKYO, "JP"), "ap-northeast")

    def test_candidates(self):
        """lists the allowed healthy regions, nearest first"""
        r = router()
        self.assertEqual(r.candidates(PARIS, "EU"), ["eu-central", "eu-west"])
        self.assertEqual(r.candidates(SINGAPORE, "SG")[:3], ["ap-south", "ap-northeast", "eu-central"])
        self.assertEqual(len(r.candidates(SINGAPORE, "SG")), 6, "SG has no residency rule")

    def test_residency(self):
        """keeps restricted users in their jurisdiction, wherever they are"""
        r = router()
        self.assertEqual(r.route(BOSTON, "EU"), "eu-west", "an EU user traveling in the US")
        self.assertEqual(r.route(BOSTON, "US"), "us-east")
        self.assertEqual(r.route(LONDON, "IN"), "ap-south")

    def test_failover(self):
        """fails over to the next allowed region when one is down"""
        r = router()
        r.mark_down("eu-central")
        self.assertEqual(r.route(PARIS, "EU"), "eu-west")
        r.mark_up("eu-central")
        self.assertEqual(r.route(PARIS, "EU"), "eu-central")

    def test_fails_closed(self):
        """refuses rather than sending restricted data abroad"""
        r = router()
        r.mark_down("eu-central")
        r.mark_down("eu-west")
        with self.assertRaises(NoRegion):
            r.route(PARIS, "EU")
        self.assertEqual(r.route(LONDON, "UK"), "us-east", "unrestricted users can cross the ocean")
        r.mark_down("ap-south")
        with self.assertRaises(NoRegion):
            r.route(MUMBAI, "IN")

    def test_spillover(self):
        """spills over to the next region with spare capacity"""
        r = router()
        self.assertEqual([r.route(NEW_YORK, "US") for _ in range(3)], ["us-east", "us-east", "us-west"])
        self.assertEqual(r.load["us-east"], 2)
        r.finish("us-east")
        self.assertEqual(r.route(NEW_YORK, "US"), "us-east")

    def test_all_full(self):
        """uses the nearest allowed region when every one is full"""
        regions = {
            "eu-west": {**REGIONS["eu-west"], "capacity": 1},
            "eu-central": {**REGIONS["eu-central"], "capacity": 1},
            "us-east": REGIONS["us-east"],
        }
        r = GlobalRouter(regions, RESIDENCY)
        self.assertEqual([r.route(PARIS, "EU") for _ in range(4)], ["eu-central", "eu-west", "eu-central", "eu-central"])
        self.assertEqual(r.load, {"eu-west": 1, "eu-central": 3, "us-east": 0})


class CounterTest(unittest.TestCase):
    def test_local(self):
        """counts up and down locally"""
        c = PNCounter("us-east")
        c.increment()
        c.increment(4)
        c.decrement(2)
        self.assertEqual(c.value(), 3)

    def test_concurrent(self):
        """keeps every region's concurrent updates"""
        us, eu = PNCounter("us-east"), PNCounter("eu-west")
        us.increment(5)
        eu.increment(3)
        eu.decrement(1)
        us.merge(eu)
        eu.merge(us)
        self.assertEqual(us.value(), 7)
        self.assertEqual(eu.value(), 7)

    def test_idempotent(self):
        """can merge the same state twice"""
        us, eu = PNCounter("us-east"), PNCounter("eu-west")
        eu.increment(3)
        us.merge(eu)
        us.merge(eu)
        self.assertEqual(us.value(), 3)
        us.merge(us)
        self.assertEqual(us.value(), 3)

    def test_order_independent(self):
        """converges whatever order merges arrive in"""
        rng = random.Random(3)
        names = ["us-east", "eu-west", "ap-south"]
        expected = 0
        replicas = {n: PNCounter(n) for n in names}
        for _ in range(60):
            c = replicas[rng.choice(names)]
            if rng.random() < 0.7:
                n = rng.randint(1, 5)
                c.increment(n)
                expected += n
            else:
                c.decrement()
                expected -= 1
            if rng.random() < 0.3:  # gossip a random pair
                a, b = rng.sample(names, 2)
                replicas[a].merge(replicas[b])
        for order in itertools.permutations(names):
            final = PNCounter("observer")
            for n in order:
                final.merge(replicas[n])
            self.assertEqual(final.value(), expected, order)

    def test_stale_state(self):
        """ignores an older copy of a region's state"""
        us, eu = PNCounter("us-east"), PNCounter("eu-west")
        eu.increment(2)
        old = PNCounter("eu-west")
        old.merge(eu)  # a copy taken at 2
        eu.increment(5)
        us.merge(eu)
        us.merge(old)  # arrives late
        self.assertEqual(us.value(), 7)


class EdgeTtlTest(unittest.TestCase):
    def test_max_age(self):
        """caches for max-age seconds"""
        self.assertEqual(edge_ttl({}, 200, {"Cache-Control": "public, max-age=31536000, immutable"}), 31536000)
        self.assertEqual(edge_ttl({}, 200, {"cache-control": "max-age=60"}), 60)

    def test_s_maxage(self):
        """prefers s-maxage, which is meant for shared caches"""
        self.assertEqual(edge_ttl({}, 200, {"Cache-Control": "max-age=0, s-maxage=5"}), 5)
        self.assertEqual(edge_ttl({}, 200, {"Cache-Control": "S-MAXAGE=10, max-age=600"}), 10)

    def test_not_shared(self):
        """never stores private, no-store, or no-cache responses"""
        for cc in ["private, max-age=600", "no-store", "no-cache, max-age=600", "max-age=600, Private"]:
            self.assertEqual(edge_ttl({}, 200, {"Cache-Control": cc}), 0, cc)

    def test_no_directive(self):
        """caches nothing the origin didn't mark cacheable"""
        self.assertEqual(edge_ttl({}, 200, {}), 0)
        self.assertEqual(edge_ttl({}, 200, {"Cache-Control": "public"}), 0)
        self.assertEqual(edge_ttl({}, 200, {"Cache-Control": "max-age=soon"}), 0)

    def test_cookies(self):
        """never caches a response that sets a cookie"""
        self.assertEqual(edge_ttl({}, 200, {"Cache-Control": "public, max-age=600", "Set-Cookie": "session=abc"}), 0)

    def test_authorization(self):
        """caches authorized requests only when the origin explicitly allows it"""
        auth = {"Authorization": "Bearer xyz"}
        self.assertEqual(edge_ttl(auth, 200, {"Cache-Control": "max-age=600"}), 0)
        self.assertEqual(edge_ttl(auth, 200, {"Cache-Control": "public, max-age=600"}), 600)
        self.assertEqual(edge_ttl(auth, 200, {"Cache-Control": "s-maxage=30"}), 30)

    def test_status(self):
        """caches only 200, 301, 404, and 410 responses"""
        cc = {"Cache-Control": "max-age=60"}
        self.assertEqual([edge_ttl({}, s, cc) for s in [200, 301, 404, 410]], [60, 60, 60, 60])
        self.assertEqual([edge_ttl({}, s, cc) for s in [201, 302, 403, 500, 503]], [0, 0, 0, 0, 0])


class CacheKeyTest(unittest.TestCase):
    def test_shape(self):
        """builds host, path, sorted query, and varied headers"""
        self.assertEqual(
            cache_key("https://CDN.Example.com/img/cat.png?w=200&fmt=webp", {"Accept-Language": "fr"}, ["Accept-Language"]),
            "cdn.example.com/img/cat.png?fmt=webp&w=200|accept-language=fr",
        )
        self.assertEqual(cache_key("https://example.com", {}), "example.com/")

    def test_query_order(self):
        """ignores query parameter order"""
        self.assertEqual(cache_key("https://a.com/p?x=1&y=2", {}), cache_key("https://a.com/p?y=2&x=1", {}))
        self.assertNotEqual(cache_key("https://a.com/p?x=1", {}), cache_key("https://a.com/p?x=2", {}))

    def test_tracking_params(self):
        """drops tracking parameters that don't change the response"""
        base = cache_key("https://a.com/sale?item=7", {})
        for url in [
            "https://a.com/sale?item=7&utm_source=newsletter&utm_campaign=fall",
            "https://a.com/sale?fbclid=abc&item=7",
            "https://a.com/sale?item=7&gclid=xyz",
        ]:
            self.assertEqual(cache_key(url, {}), base, url)

    def test_vary(self):
        """keeps separate copies per value of each Vary header"""
        url = "https://a.com/"
        en = cache_key(url, {"Accept-Language": "en"}, ["Accept-Language"])
        de = cache_key(url, {"accept-language": "de"}, ["accept-language"])
        self.assertNotEqual(en, de)
        self.assertEqual(cache_key(url, {"Accept-Language": "en"}), cache_key(url, {"Accept-Language": "de"}), "no Vary")
        self.assertEqual(
            cache_key(url, {"A": "1", "B": "2"}, ["B", "a"]),
            cache_key(url, {"a": "1", "b": "2"}, ["A", "b"]),
        )
        self.assertIsNone(cache_key(url, {}, ["*"]))

    def test_encoding(self):
        """normalizes Accept-Encoding so caches don't fragment"""
        url = "https://a.com/app.js"
        keys = {
            cache_key(url, {"Accept-Encoding": ae}, ["Accept-Encoding"])
            for ae in ["gzip, deflate, br", "br, gzip", "br;q=1.0, gzip;q=0.8", "BR"]
        }
        self.assertEqual(keys, {"a.com/app.js|accept-encoding=br"})
        self.assertEqual(cache_key(url, {"Accept-Encoding": "gzip, deflate"}, ["Accept-Encoding"]), "a.com/app.js|accept-encoding=gzip")
        self.assertEqual(cache_key(url, {}, ["Accept-Encoding"]), "a.com/app.js|accept-encoding=identity")


if __name__ == "__main__":
    unittest.main()
