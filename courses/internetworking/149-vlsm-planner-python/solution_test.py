import unittest

from solution import hosts_to_prefix, parse_cidr, split, subnet_info, vlsm


class Sizing(unittest.TestCase):
    def test_hosts_to_prefix(self):
        """The smallest prefix where 2^h - 2 covers the hosts"""
        cases = {1: 30, 2: 30, 3: 29, 6: 29, 7: 28, 14: 28, 15: 27, 30: 27, 50: 26,
                 62: 26, 63: 25, 100: 25, 126: 25, 127: 24, 254: 24, 300: 23, 500: 23, 1000: 22, 4094: 20}
        for hosts, prefix in cases.items():
            with self.subTest(hosts=hosts):
                self.assertEqual(hosts_to_prefix(hosts), prefix)

    def test_hosts_to_prefix_rejects_zero(self):
        """A subnet for no hosts is an error"""
        for bad in [0, -5]:
            with self.subTest(hosts=bad):
                with self.assertRaises(ValueError):
                    hosts_to_prefix(bad)

    def test_parse_cidr(self):
        """A network in CIDR notation becomes (integer, prefix)"""
        self.assertEqual(parse_cidr("10.1.1.64/26"), (167837952 + 64, 26))
        self.assertEqual(parse_cidr("23.0.0.0/8"), (23 << 24, 8))
        self.assertEqual(parse_cidr("166.21.16.0/20"), ((166 << 24) | (21 << 16) | (16 << 8), 20))

    def test_parse_cidr_rejects_bad_input(self):
        """Host bits set, or a bad prefix, raise ValueError"""
        for bad in ["10.1.1.8/28", "166.23.9.18/28", "10.1.1.0/33", "10.1.1.0/x", "10.1.1.0", "10.1.1.0/-1"]:
            with self.subTest(cidr=bad):
                with self.assertRaises(ValueError):
                    parse_cidr(bad)


class OneSubnet(unittest.TestCase):
    def test_slash_28(self):
        """166.23.9.16/28, from the worked examples"""
        self.assertEqual(subnet_info("166.23.9.16/28"), {
            "network": "166.23.9.16", "broadcast": "166.23.9.31", "mask": "255.255.255.240",
            "gateway": "166.23.9.17", "last_host": "166.23.9.30", "hosts": 14,
        })

    def test_slash_20(self):
        """166.21.16.0/20 reaches into the 3rd octet"""
        self.assertEqual(subnet_info("166.21.16.0/20"), {
            "network": "166.21.16.0", "broadcast": "166.21.31.255", "mask": "255.255.240.0",
            "gateway": "166.21.16.1", "last_host": "166.21.31.254", "hosts": 4094,
        })

    def test_class_a(self):
        """23.0.0.0/8 as one network"""
        info = subnet_info("23.0.0.0/8")
        self.assertEqual(info["broadcast"], "23.255.255.255")
        self.assertEqual(info["mask"], "255.0.0.0")
        self.assertEqual(info["hosts"], 16777214)

    def test_router_link(self):
        """A /30 has one address for each router"""
        info = subnet_info("10.1.1.4/30")
        self.assertEqual((info["gateway"], info["last_host"], info["broadcast"]), ("10.1.1.5", "10.1.1.6", "10.1.1.7"))
        self.assertEqual(info["hosts"], 2)


class ManySubnets(unittest.TestCase):
    def test_split_into_slash_26(self):
        """Four equal /26s, subnet zero included"""
        self.assertEqual(split("10.1.1.0/24", 26),
                         ["10.1.1.0/26", "10.1.1.64/26", "10.1.1.128/26", "10.1.1.192/26"])

    def test_split_class_a_into_class_bs(self):
        """23.0.0.0/8 into 256 /16s"""
        nets = split("23.0.0.0/8", 16)
        self.assertEqual(len(nets), 256)
        self.assertEqual(nets[0], "23.0.0.0/16")
        self.assertEqual(nets[40], "23.40.0.0/16")
        self.assertEqual(nets[-1], "23.255.0.0/16")

    def test_split_same_size(self):
        """Splitting into the same prefix gives the network back"""
        self.assertEqual(split("192.168.5.0/24", 24), ["192.168.5.0/24"])

    def test_split_rejects_bad_prefix(self):
        """Can't split into something bigger, or smaller than a /30"""
        for p in [23, 31, 32]:
            with self.subTest(new_prefix=p):
                with self.assertRaises(ValueError):
                    split("10.1.1.0/24", p)

    def test_vlsm_reading_example(self):
        """The five subnets from the VLSM reading"""
        needs = [("Router link 1", 2), ("Staff", 100), ("Printers & servers", 12), ("Lab", 50), ("Router link 2", 2)]
        self.assertEqual(vlsm("10.1.1.0/24", needs), [
            ("Staff", "10.1.1.0/25"),
            ("Lab", "10.1.1.128/26"),
            ("Printers & servers", "10.1.1.192/28"),
            ("Router link 1", "10.1.1.208/30"),
            ("Router link 2", "10.1.1.212/30"),
        ])

    def test_vlsm_drill(self):
        """The plan from the VLSM drill"""
        needs = [("Management", 10), ("Sales", 60), ("Link", 2), ("Engineering", 28)]
        self.assertEqual(vlsm("172.16.5.0/24", needs), [
            ("Sales", "172.16.5.0/26"),
            ("Engineering", "172.16.5.64/27"),
            ("Management", "172.16.5.96/28"),
            ("Link", "172.16.5.112/30"),
        ])

    def test_vlsm_project_example(self):
        """The one-class-C office from the project reading"""
        needs = [("Guests", 50), ("Staff", 100), ("Servers", 10), ("Cameras", 20), ("Link", 2)]
        self.assertEqual(vlsm("192.168.10.0/24", needs), [
            ("Staff", "192.168.10.0/25"),
            ("Guests", "192.168.10.128/26"),
            ("Cameras", "192.168.10.192/27"),
            ("Servers", "192.168.10.224/28"),
            ("Link", "192.168.10.240/30"),
        ])

    def test_vlsm_inside_a_bigger_block(self):
        """Allocation starts at the given network, not at .0"""
        self.assertEqual(vlsm("10.8.4.0/22", [("A", 300), ("B", 300)]),
                         [("A", "10.8.4.0/23"), ("B", "10.8.6.0/23")])

    def test_vlsm_too_big(self):
        """Needs that don't fit raise ValueError"""
        with self.assertRaises(ValueError):
            vlsm("10.1.1.0/24", [("Staff", 200), ("Lab", 100)])
        with self.assertRaises(ValueError):
            vlsm("10.1.1.0/24", [("Everyone", 300)])


if __name__ == "__main__":
    unittest.main()
