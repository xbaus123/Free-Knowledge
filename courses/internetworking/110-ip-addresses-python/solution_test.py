import unittest

from solution import (
    address_class,
    broadcast_address,
    int_to_ip,
    ip_to_int,
    is_loopback,
    is_private,
    mask_to_prefix,
    network_address,
    prefix_to_mask,
    same_subnet,
    usable_hosts,
)


class Converting(unittest.TestCase):
    def test_ip_to_int(self):
        """Dotted decimal becomes a 32-bit integer"""
        self.assertEqual(ip_to_int("192.168.1.15"), 3232235791)
        self.assertEqual(ip_to_int("0.0.0.0"), 0)
        self.assertEqual(ip_to_int("255.255.255.255"), 2**32 - 1)
        self.assertEqual(ip_to_int("10.0.0.1"), 10 * 2**24 + 1)

    def test_int_to_ip(self):
        """A 32-bit integer becomes dotted decimal"""
        self.assertEqual(int_to_ip(3232235791), "192.168.1.15")
        self.assertEqual(int_to_ip(0), "0.0.0.0")
        self.assertEqual(int_to_ip(2**32 - 1), "255.255.255.255")

    def test_round_trip(self):
        """Converting there and back gives the same address"""
        for ip in ["127.0.0.1", "172.20.10.2", "224.0.0.251", "1.2.3.4"]:
            self.assertEqual(int_to_ip(ip_to_int(ip)), ip)

    def test_rejects_bad_addresses(self):
        """Anything but four octets from 0 to 255 raises ValueError"""
        for bad in ["10.0.0", "1.2.3.4.5", "1.2.3.256", "a.b.c.d", "1..2.3", "1.2.3.-4", ""]:
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    ip_to_int(bad)


class Kinds(unittest.TestCase):
    def test_classes(self):
        """The class comes from the first octet"""
        cases = {
            "10.104.216.118": "A", "127.0.0.1": "A", "128.0.0.1": "B", "150.20.3.4": "B",
            "191.255.0.1": "B", "192.168.86.1": "C", "223.1.1.1": "C", "224.0.0.251": "D",
            "239.255.255.255": "D", "240.0.0.1": "E", "255.255.255.255": "E",
        }
        for ip, cls in cases.items():
            with self.subTest(ip=ip):
                self.assertEqual(address_class(ip), cls)

    def test_private(self):
        """The three RFC 1918 ranges are private, and only those"""
        for ip in ["10.0.0.1", "10.255.255.255", "172.16.0.1", "172.20.10.2", "172.31.255.255",
                   "192.168.0.1", "192.168.255.254"]:
            with self.subTest(ip=ip):
                self.assertTrue(is_private(ip))
        for ip in ["9.255.255.255", "11.0.0.1", "172.15.255.255", "172.32.0.1", "192.167.1.1",
                   "192.169.0.1", "8.8.8.8", "127.0.0.1"]:
            with self.subTest(ip=ip):
                self.assertFalse(is_private(ip))

    def test_loopback(self):
        """The whole 127 network is loopback"""
        self.assertTrue(is_loopback("127.0.0.1"))
        self.assertTrue(is_loopback("127.255.0.9"))
        self.assertFalse(is_loopback("126.0.0.1"))
        self.assertFalse(is_loopback("128.0.0.1"))


class Masks(unittest.TestCase):
    def test_prefix_to_mask(self):
        """Prefix lengths become masks"""
        cases = {0: "0.0.0.0", 8: "255.0.0.0", 16: "255.255.0.0", 22: "255.255.252.0",
                 24: "255.255.255.0", 26: "255.255.255.192", 30: "255.255.255.252", 32: "255.255.255.255"}
        for p, mask in cases.items():
            with self.subTest(prefix=p):
                self.assertEqual(prefix_to_mask(p), mask)

    def test_mask_to_prefix(self):
        """Masks become prefix lengths"""
        self.assertEqual(mask_to_prefix("255.255.252.0"), 22)
        self.assertEqual(mask_to_prefix("255.255.255.0"), 24)
        self.assertEqual(mask_to_prefix("255.255.255.240"), 28)
        self.assertEqual(mask_to_prefix("0.0.0.0"), 0)
        self.assertEqual(mask_to_prefix("255.255.255.255"), 32)

    def test_rejects_bad_masks(self):
        """A 1 after a 0 isn't a mask"""
        for bad in ["255.0.255.0", "255.255.255.250", "0.255.255.255", "255.255.0.1"]:
            with self.subTest(mask=bad):
                with self.assertRaises(ValueError):
                    mask_to_prefix(bad)


class Subnets(unittest.TestCase):
    def test_reading_example(self):
        """192.168.10.77/26, from the subnetting lesson"""
        self.assertEqual(network_address("192.168.10.77", 26), "192.168.10.64")
        self.assertEqual(broadcast_address("192.168.10.77", 26), "192.168.10.127")

    def test_campus_wifi(self):
        """The ipconfig example: 10.104.216.118/22"""
        self.assertEqual(network_address("10.104.216.118", 22), "10.104.216.0")
        self.assertEqual(broadcast_address("10.104.216.118", 22), "10.104.219.255")

    def test_drill(self):
        """172.16.45.200/20, from the drill"""
        self.assertEqual(network_address("172.16.45.200", 20), "172.16.32.0")
        self.assertEqual(broadcast_address("172.16.45.200", 20), "172.16.47.255")

    def test_edges(self):
        """/32 is one address, /0 is everything"""
        self.assertEqual(network_address("1.2.3.4", 32), "1.2.3.4")
        self.assertEqual(broadcast_address("1.2.3.4", 32), "1.2.3.4")
        self.assertEqual(network_address("1.2.3.4", 0), "0.0.0.0")
        self.assertEqual(broadcast_address("1.2.3.4", 0), "255.255.255.255")

    def test_usable_hosts(self):
        """2^h - 2, with the /31 and /32 exceptions"""
        cases = {8: 16777214, 16: 65534, 22: 1022, 24: 254, 26: 62, 30: 2, 31: 2, 32: 1}
        for p, n in cases.items():
            with self.subTest(prefix=p):
                self.assertEqual(usable_hosts(p), n)

    def test_same_subnet(self):
        """The decision a host makes before sending"""
        self.assertTrue(same_subnet("10.1.1.20", "10.1.1.24", 24))
        self.assertFalse(same_subnet("10.1.1.20", "10.1.2.35", 24))
        self.assertTrue(same_subnet("10.1.1.20", "10.1.2.35", 16))
        self.assertTrue(same_subnet("192.168.1.65", "192.168.1.94", 27))
        self.assertFalse(same_subnet("192.168.1.95", "192.168.1.96", 27))
        self.assertTrue(same_subnet("10.104.216.118", "10.104.216.2", 22))


if __name__ == "__main__":
    unittest.main()
