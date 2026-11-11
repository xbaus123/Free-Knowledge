import unittest

from solution import BROADCAST, STP_COST, LearningSwitch, bridge_id, elect_root, path_cost, root_port

A = "aa:aa:aa:aa:aa:aa"
B = "bb:bb:bb:bb:bb:bb"
C = "cc:cc:cc:cc:cc:cc"


class Learning(unittest.TestCase):
    def test_learns_source(self):
        """The source MAC is learned on the port it came in on"""
        sw = LearningSwitch([1, 2, 3, 4])
        sw.receive(1, A, C)
        self.assertEqual(sw.table, {A: 1})

    def test_floods_unknown(self):
        """An unknown destination is flooded out of every other port"""
        sw = LearningSwitch([1, 2, 3, 4])
        self.assertEqual(sw.receive(1, A, C), [2, 3, 4])

    def test_forwards_known(self):
        """The reply goes out of exactly one port"""
        sw = LearningSwitch([1, 2, 3, 4])
        sw.receive(1, A, C)
        self.assertEqual(sw.receive(3, C, A), [1])
        self.assertEqual(sw.receive(1, A, C), [3])
        self.assertEqual(sw.table, {A: 1, C: 3})

    def test_broadcast_always_floods(self):
        """Broadcasts flood even when every host is known"""
        sw = LearningSwitch([1, 2, 3])
        sw.receive(1, A, B)
        sw.receive(2, B, A)
        self.assertEqual(sw.receive(2, B, BROADCAST), [1, 3])

    def test_filters_same_port(self):
        """A destination on the incoming port is filtered"""
        sw = LearningSwitch([1, 2, 3])
        sw.receive(2, A, BROADCAST)
        self.assertEqual(sw.receive(2, B, A), [])

    def test_host_moves(self):
        """A host seen on a new port is relearned there"""
        sw = LearningSwitch([1, 2, 3])
        sw.receive(1, A, BROADCAST)
        sw.receive(3, A, BROADCAST)
        self.assertEqual(sw.table[A], 3)
        self.assertEqual(sw.receive(2, B, A), [3])

    def test_case_insensitive(self):
        """MAC addresses are compared in lower case"""
        sw = LearningSwitch([1, 2])
        sw.receive(1, A.upper(), BROADCAST)
        self.assertEqual(sw.table, {A: 1})
        self.assertEqual(sw.receive(2, B, A.upper()), [1])
        self.assertEqual(sw.receive(1, A, BROADCAST.upper()), [2])

    def test_unsorted_ports(self):
        """Flooding lists ports in increasing order"""
        sw = LearningSwitch([4, 1, 3, 2])
        self.assertEqual(sw.receive(3, A, B), [1, 2, 4])

    def test_forget(self):
        """After aging out, the host is flooded to again"""
        sw = LearningSwitch([1, 2, 3])
        sw.receive(1, A, BROADCAST)
        sw.forget(A.upper())
        self.assertEqual(sw.table, {})
        self.assertEqual(sw.receive(2, B, A), [1, 3])
        sw.forget(C)  # not in the table: nothing happens


class BridgeId(unittest.TestCase):
    def test_value(self):
        """Priority in the top bits, MAC in the low 48"""
        self.assertEqual(bridge_id(32768, "00:00:00:00:00:01"), 32768 * 2**48 + 1)
        self.assertEqual(bridge_id(0, "ff:ff:ff:ff:ff:ff"), 2**48 - 1)

    def test_priority_beats_mac(self):
        """A lower priority wins whatever the MACs"""
        self.assertLess(bridge_id(28672, "ff:ff:ff:ff:ff:ff"), bridge_id(32768, "00:00:00:00:00:00"))


class ElectRoot(unittest.TestCase):
    def test_triangle(self):
        """The reading's triangle: equal priorities, lowest MAC wins"""
        bridges = {
            "SW1": (32768, "00:00:00:00:0a:aa"),
            "SW2": (32768, "00:00:00:00:0b:bb"),
            "SW3": (32768, "00:00:00:00:0c:cc"),
        }
        self.assertEqual(elect_root(bridges), "SW1")

    def test_priority_first(self):
        """Priority is compared before the MAC"""
        bridges = {"A": (32768, "00:00:00:00:00:01"), "B": (28672, "00:ff:ff:ff:ff:ff")}
        self.assertEqual(elect_root(bridges), "B")

    def test_drill_three(self):
        """The drill's three-switch question"""
        bridges = {
            "A": (4096, "00:00:00:00:00:99"),
            "B": (8192, "00:00:00:00:00:01"),
            "C": (4096, "00:00:00:00:00:50"),
        }
        self.assertEqual(elect_root(bridges), "C")

    def test_empty(self):
        """No bridges, no root"""
        self.assertIsNone(elect_root({}))


class Costs(unittest.TestCase):
    def test_path_cost(self):
        """Costs add up along the path"""
        self.assertEqual(path_cost([100]), 19)
        self.assertEqual(path_cost([1000, 1000]), 8)
        self.assertEqual(path_cost([10, 100, 10000]), 121)
        self.assertEqual(path_cost([]), 0)

    def test_root_port_cheapest(self):
        """Two gigabit hops beat one 100 Mbps hop"""
        self.assertEqual(root_port({"Fa0/0": [100], "Gi0/1": [1000, 1000]}), "Gi0/1")

    def test_root_port_tie(self):
        """On a tie, the port name that sorts first"""
        self.assertEqual(root_port({"Gi0/2": [1000], "Gi0/1": [1000]}), "Gi0/1")

    def test_root_port_empty(self):
        """No ports, no root port"""
        self.assertIsNone(root_port({}))

    def test_cost_table(self):
        """The cost table is unchanged"""
        self.assertEqual(STP_COST[1000], 4)


if __name__ == "__main__":
    unittest.main()
