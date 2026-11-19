import heapq
import random
import unittest
from collections import Counter

from solution import (
    Gateway,
    LeastConnections,
    NoHealthyServers,
    PowerOfTwoChoices,
    RoundRobin,
    WeightedRoundRobin,
)


def picks(lb, n):
    return [lb.pick() for _ in range(n)]


class HealthTest(unittest.TestCase):
    def test_round_robin(self):
        """round robin takes turns"""
        self.assertEqual(picks(RoundRobin(["a", "b", "c"]), 7), ["a", "b", "c", "a", "b", "c", "a"])

    def test_ejects_after_consecutive_failures(self):
        """takes a server out of rotation after 3 failures in a row"""
        lb = RoundRobin(["a", "b", "c"])
        lb.report("b", False)
        lb.report("b", False)
        lb.report("b", True)  # a success resets the count
        lb.report("b", False)
        lb.report("b", False)
        self.assertIn("b", picks(lb, 6), "b has only failed twice in a row")
        lb.report("b", False)
        self.assertEqual(lb.healthy(), ["a", "c"])
        self.assertNotIn("b", picks(lb, 10))
        self.assertEqual(Counter(picks(lb, 10)), {"a": 5, "c": 5})

    def test_mark_up(self):
        """puts a server back once a health check passes"""
        lb = RoundRobin(["a", "b"], max_failures=1)
        lb.report("a", False)
        self.assertEqual(picks(lb, 3), ["b", "b", "b"])
        lb.mark_up("a")
        self.assertEqual(Counter(picks(lb, 4)), {"a": 2, "b": 2})
        lb.report("a", False)
        self.assertEqual(lb.healthy(), ["b"], "a fresh failure count after coming back")

    def test_no_healthy_servers(self):
        """raises NoHealthyServers when every server is down"""
        lb = LeastConnections(["a", "b"], max_failures=1)
        lb.report("a", False)
        lb.report("b", False)
        with self.assertRaises(NoHealthyServers):
            lb.pick()


class WeightedTest(unittest.TestCase):
    def test_smooth_sequence(self):
        """spreads a heavy server's turns out instead of bunching them"""
        lb = WeightedRoundRobin({"a": 5, "b": 1, "c": 1})
        self.assertEqual(picks(lb, 7), ["a", "a", "b", "a", "c", "a", "a"])
        self.assertEqual(picks(WeightedRoundRobin({"a": 3, "b": 2}), 5), ["a", "b", "a", "b", "a"])

    def test_proportions(self):
        """sends traffic in proportion to the weights"""
        lb = WeightedRoundRobin({"big": 4, "medium": 2, "small": 1})
        self.assertEqual(Counter(picks(lb, 70)), {"big": 40, "medium": 20, "small": 10})

    def test_skips_unhealthy(self):
        """shares the traffic among the healthy servers"""
        lb = WeightedRoundRobin({"a": 2, "b": 1, "c": 1}, max_failures=1)
        lb.report("a", False)
        self.assertEqual(Counter(picks(lb, 10)), {"b": 5, "c": 5})


class LeastConnectionsTest(unittest.TestCase):
    def test_picks_least_busy(self):
        """picks the server with the fewest active requests"""
        lb = LeastConnections(["a", "b", "c"])
        self.assertEqual(picks(lb, 3), ["a", "b", "c"], "ties go to the first server in the list")
        lb.release("b")
        self.assertEqual(lb.pick(), "b")
        lb.release("a")
        lb.release("c")
        self.assertEqual(picks(lb, 2), ["a", "c"])
        self.assertEqual(lb.active, {"a": 1, "b": 1, "c": 1})

    def test_slow_server(self):
        """beats round robin when one server is slow"""

        def mean_response(lb):
            duration = {"fast-1": 10, "fast-2": 10, "slow": 100}
            finishing, total = [], 0
            for now in range(0, 4000, 4):  # a request every 4 ticks
                while finishing and finishing[0][0] <= now:
                    lb.release(heapq.heappop(finishing)[1])
                server = lb.pick()
                total += duration[server]
                heapq.heappush(finishing, (now + duration[server], server))
            return total / 1000

        servers = ["fast-1", "fast-2", "slow"]
        rr, lc = mean_response(RoundRobin(servers)), mean_response(LeastConnections(servers))
        self.assertAlmostEqual(rr, 40, delta=1, msg="round robin sends a third of the requests to the slow server")
        self.assertLess(lc, 20, f"least connections should steer around the slow server (got {lc:.1f})")


class PowerOfTwoTest(unittest.TestCase):
    def test_compares_two_samples(self):
        """samples two servers and picks the less busy"""
        servers = ["a", "b", "c", "d"]
        lb = PowerOfTwoChoices(servers, random.Random(5))
        lb.active.update({"a": 5, "b": 0, "c": 3, "d": 1})
        mirror, active = random.Random(5), {"a": 5, "b": 0, "c": 3, "d": 1}
        for _ in range(20):
            x, y = mirror.sample(servers, 2)
            want = y if active[y] < active[x] else x
            active[want] += 1
            self.assertEqual(lb.pick(), want)
        self.assertEqual(lb.active, active)

    def test_one_healthy(self):
        """uses the only healthy server"""
        lb = PowerOfTwoChoices(["a", "b"], random.Random(1), max_failures=1)
        lb.report("a", False)
        self.assertEqual(picks(lb, 3), ["b", "b", "b"])


class GatewayTest(unittest.TestCase):
    def setUp(self):
        self.users = RoundRobin(["users-1", "users-2"], max_failures=1)
        self.orders = RoundRobin(["orders-1"], max_failures=1)
        self.admin = RoundRobin(["admin-1"])
        self.gw = Gateway({"/api/users": self.users, "/api/orders": self.orders, "/api/users/admin": self.admin}, {"key-1"})
        self.auth = {"Authorization": "Bearer key-1"}

    def test_routes_by_prefix(self):
        """routes by the longest matching path prefix"""
        self.assertEqual(self.gw.handle("/api/users/42", self.auth), (200, "users-1"))
        self.assertEqual(self.gw.handle("/api/users", self.auth), (200, "users-2"))
        self.assertEqual(self.gw.handle("/api/orders/7/items", self.auth), (200, "orders-1"))
        self.assertEqual(self.gw.handle("/api/users/admin/audit", self.auth), (200, "admin-1"))

    def test_whole_segments(self):
        """matches whole path segments only"""
        self.assertEqual(self.gw.handle("/api/usersettings", self.auth), (404, None))
        self.assertEqual(self.gw.handle("/api", self.auth), (404, None))
        self.assertEqual(self.gw.handle("/health", self.auth), (404, None))

    def test_authenticates(self):
        """rejects requests without a valid bearer token"""
        for headers in ({}, {"Authorization": "Bearer nope"}, {"Authorization": "key-1"}, {"Authorization": "Basic key-1"}):
            self.assertEqual(self.gw.handle("/api/users/1", headers), (401, None), headers)

    def test_no_healthy_upstream(self):
        """answers 503 when a route has no healthy servers"""
        self.orders.report("orders-1", False)
        self.assertEqual(self.gw.handle("/api/orders/7", self.auth), (503, None))
        self.assertEqual(self.gw.handle("/api/users/1", self.auth)[0], 200)


if __name__ == "__main__":
    unittest.main()
