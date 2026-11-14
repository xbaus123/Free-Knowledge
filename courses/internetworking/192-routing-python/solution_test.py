import unittest

from solution import accept_path, dijkstra, dv_update, lookup, origin_validate, prepend

# The forwarding table from the longest prefix match reading.
READING_TABLE = [
    ("200.23.16.0/21", 0),
    ("200.23.24.0/24", 1),
    ("200.23.24.0/21", 2),
    ("0.0.0.0/0", 3),
]

# The table from the longest prefix match drill.
DRILL_TABLE = [
    ("0.0.0.0/0", "E"),
    ("10.0.0.0/8", "A"),
    ("10.1.0.0/16", "B"),
    ("10.1.2.0/24", "C"),
    ("10.1.2.128/25", "D"),
]

# The network from the distance vector and link state readings.
GRAPH = {
    "A": {"B": 1, "C": 4},
    "B": {"A": 1, "C": 2, "D": 5},
    "C": {"A": 4, "B": 2, "D": 1},
    "D": {"B": 5, "C": 1, "E": 3},
    "E": {"D": 3},
}


class LongestPrefixMatch(unittest.TestCase):
    def test_reading_examples(self):
        """200.23.22.161 -> 0 and 200.23.24.170 -> 1, as in the reading"""
        self.assertEqual(lookup(READING_TABLE, "200.23.22.161"), 0)
        self.assertEqual(lookup(READING_TABLE, "200.23.24.170"), 1)

    def test_reading_check(self):
        """The destinations from the check quiz"""
        self.assertEqual(lookup(READING_TABLE, "200.23.20.5"), 0)
        self.assertEqual(lookup(READING_TABLE, "200.23.24.9"), 1)
        self.assertEqual(lookup(READING_TABLE, "200.23.31.200"), 2)

    def test_default_route(self):
        """Nothing else matches, so the default route wins"""
        self.assertEqual(lookup(READING_TABLE, "10.0.0.1"), 3)

    def test_drill(self):
        """The order of the table doesn't matter: the longest match wins"""
        cases = {"10.1.2.200": "D", "10.1.2.50": "C", "10.1.99.1": "B", "10.200.0.1": "A", "172.16.0.1": "E"}
        for dst, hop in cases.items():
            with self.subTest(destination=dst):
                self.assertEqual(lookup(DRILL_TABLE, dst), hop)

    def test_no_route(self):
        """Without a default route, an unmatched destination gives None"""
        self.assertIsNone(lookup(DRILL_TABLE[1:], "172.16.0.1"))
        self.assertIsNone(lookup([], "10.0.0.1"))

    def test_hijack(self):
        """A more specific announcement steals the traffic"""
        hijacked = DRILL_TABLE + [("10.1.2.0/25", "attacker")]
        self.assertEqual(lookup(hijacked, "10.1.2.50"), "attacker")
        self.assertEqual(lookup(hijacked, "10.1.2.200"), "D")

    def test_host_route(self):
        """A /32 matches exactly one address"""
        table = [("10.0.0.0/8", "A"), ("10.9.9.9/32", "H")]
        self.assertEqual(lookup(table, "10.9.9.9"), "H")
        self.assertEqual(lookup(table, "10.9.9.8"), "A")


class Dijkstra(unittest.TestCase):
    def test_from_a(self):
        """The worked example: every first hop from A is B"""
        self.assertEqual(dijkstra(GRAPH, "A"), {
            "B": (1, "B"), "C": (3, "B"), "D": (4, "B"), "E": (7, "B"),
        })

    def test_from_c(self):
        """From C, E costs 4 through D"""
        result = dijkstra(GRAPH, "C")
        self.assertEqual(result["E"], (4, "D"))
        self.assertEqual(result["A"], (3, "B"))
        self.assertNotIn("C", result)

    def test_drill_network(self):
        """The drill's network: P to S costs 6, starting through Q"""
        graph = {
            "P": {"Q": 2, "R": 6},
            "Q": {"P": 2, "R": 3, "S": 7},
            "R": {"P": 6, "Q": 3, "S": 1},
            "S": {"Q": 7, "R": 1},
        }
        self.assertEqual(dijkstra(graph, "P"), {"Q": (2, "Q"), "R": (5, "Q"), "S": (6, "Q")})
        self.assertEqual(dijkstra(graph, "Q")["S"], (4, "R"))

    def test_unreachable(self):
        """Routers you can't reach are left out"""
        graph = {"A": {"B": 1}, "B": {"A": 1}, "C": {}}
        self.assertEqual(dijkstra(graph, "A"), {"B": (1, "B")})


class DistanceVector(unittest.TestCase):
    def test_reading_example(self):
        """A hears from B and C and picks D at cost 4 through B"""
        links = {"B": 1, "C": 4}
        vectors = {
            "B": {"A": 1, "C": 2, "D": 3, "E": 6},
            "C": {"A": 3, "B": 2, "D": 1, "E": 4},
        }
        self.assertEqual(dv_update("A", links, vectors), {
            "B": (1, "B"), "C": (3, "B"), "D": (4, "B"), "E": (7, "B"),
        })

    def test_neighbors_without_vectors(self):
        """A neighbor you haven't heard from yet is still reachable over its link"""
        self.assertEqual(dv_update("A", {"B": 2, "C": 5}, {}), {"B": (2, "B"), "C": (5, "C")})

    def test_ties_go_to_the_first_neighbor_alphabetically(self):
        """Equal costs: pick the neighbor whose name sorts first"""
        links = {"Y": 1, "X": 1}
        vectors = {"Y": {"Z": 2}, "X": {"Z": 2}}
        self.assertEqual(dv_update("W", links, vectors)["Z"], (3, "X"))

    def test_rip_infinity(self):
        """Costs of 16 or more mean unreachable, so they're left out"""
        links = {"B": 1}
        vectors = {"B": {"C": 15, "D": 14, "X": 16}}
        table = dv_update("A", links, vectors)
        self.assertNotIn("C", table)
        self.assertNotIn("X", table)
        self.assertEqual(table["D"], (15, "B"))

    def test_count_to_infinity_step(self):
        """B's link to C is gone; A still claims C at 2, so B wrongly picks 3 via A"""
        self.assertEqual(dv_update("B", {"A": 1}, {"A": {"B": 1, "C": 2}}), {"A": (1, "A"), "C": (3, "A")})


class PathVector(unittest.TestCase):
    def test_accept_path(self):
        """Reject any path that already contains your own AS"""
        self.assertTrue(accept_path(64501, [64502, 64500]))
        self.assertFalse(accept_path(64501, [64502, 64501, 64500]))
        self.assertTrue(accept_path(64501, []))

    def test_prepend(self):
        """Each AS adds itself to the front of the path"""
        self.assertEqual(prepend(64501, [64500]), [64501, 64500])
        self.assertEqual(prepend(64502, prepend(64501, [64500])), [64502, 64501, 64500])

    def test_prepend_does_not_change_the_original(self):
        """The path you received stays as it was"""
        path = [64500]
        prepend(64501, path)
        self.assertEqual(path, [64500])


class OriginValidation(unittest.TestCase):
    ROAS = [("203.0.113.0/24", 25, 64500)]

    def test_drill_cases(self):
        """The cases from the BGP security drill"""
        self.assertEqual(origin_validate(self.ROAS, "203.0.113.0/25", 64500), "valid")
        self.assertEqual(origin_validate(self.ROAS, "203.0.113.128/25", 64999), "invalid")
        self.assertEqual(origin_validate(self.ROAS, "198.51.100.0/24", 64999), "not found")

    def test_exact_prefix(self):
        """The ROA's own prefix from the right AS is valid"""
        self.assertEqual(origin_validate(self.ROAS, "203.0.113.0/24", 64500), "valid")

    def test_too_specific(self):
        """Right AS, but longer than the ROA's max length, is invalid"""
        self.assertEqual(origin_validate(self.ROAS, "203.0.113.0/26", 64500), "invalid")

    def test_less_specific_is_not_covered(self):
        """A /23 is bigger than the ROA's /24, so the ROA doesn't cover it"""
        self.assertEqual(origin_validate(self.ROAS, "203.0.112.0/23", 64500), "not found")

    def test_any_matching_roa_is_enough(self):
        """With two ROAs for the same space, matching either one is valid"""
        roas = [("203.0.113.0/24", 24, 64500), ("203.0.113.0/24", 24, 64510)]
        self.assertEqual(origin_validate(roas, "203.0.113.0/24", 64510), "valid")
        self.assertEqual(origin_validate(roas, "203.0.113.0/24", 64999), "invalid")


if __name__ == "__main__":
    unittest.main()
