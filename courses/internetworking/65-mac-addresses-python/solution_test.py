import unittest

from solution import (
    VENDORS,
    describe,
    is_broadcast,
    is_locally_administered,
    is_multicast,
    normalize_mac,
    oui,
)

CANON = "01:00:5e:00:00:fb"


class NormalizeMac(unittest.TestCase):
    def test_colons(self):
        """Colon-separated lowercase is already normal"""
        self.assertEqual(normalize_mac("01:00:5e:00:00:fb"), CANON)

    def test_windows_dashes_and_capitals(self):
        """Windows style, with dashes and capitals"""
        self.assertEqual(normalize_mac("01-00-5E-00-00-FB"), CANON)

    def test_cisco_dots(self):
        """Cisco style, three dotted groups of four"""
        self.assertEqual(normalize_mac("0100.5e00.00fb"), CANON)

    def test_bare_hex(self):
        """Twelve bare hex digits"""
        self.assertEqual(normalize_mac("01005E0000FB"), CANON)

    def test_macos_drops_leading_zeros(self):
        """macOS arp -a writes 1:0:5e:0:0:fb"""
        self.assertEqual(normalize_mac("1:0:5e:0:0:fb"), CANON)
        self.assertEqual(normalize_mac("0:0:5e:0:1:33"), "00:00:5e:00:01:33")

    def test_surrounding_spaces(self):
        """Spaces around the address are ignored"""
        self.assertEqual(normalize_mac("  3C:BD:C5:40:77:61 \n"), "3c:bd:c5:40:77:61")

    def test_rejects_bad_addresses(self):
        """Wrong lengths, long octets, and non-hex characters raise ValueError"""
        bad = [
            "",
            "01:00:5e:00:00",
            "01:00:5e:00:00:fb:aa",
            "01:00:5e:00:00:fbb",
            "01:00:5e:00:00:fg",
            "0100.5e00.00f",
            "01005e0000f",
            "zz005e0000fb",
            "01::5e:00:00:fb",
        ]
        for text in bad:
            with self.assertRaises(ValueError, msg=f"normalize_mac({text!r}) should raise ValueError"):
                normalize_mac(text)


class Oui(unittest.TestCase):
    def test_oui(self):
        """The OUI is the first three octets"""
        self.assertEqual(oui("3c:bd:c5:40:77:61"), "3c:bd:c5")

    def test_oui_any_format(self):
        """The OUI comes out normalized whatever the input format"""
        self.assertEqual(oui("3C-BD-C5-40-77-61"), "3c:bd:c5")
        self.assertEqual(oui("0:0:5e:0:1:33"), "00:00:5e")


class SpecialBits(unittest.TestCase):
    def test_broadcast(self):
        """Only all ones is broadcast"""
        self.assertTrue(is_broadcast("ff:ff:ff:ff:ff:ff"))
        self.assertTrue(is_broadcast("FFFF.FFFF.FFFF"))
        self.assertFalse(is_broadcast("ff:ff:ff:ff:ff:fe"))

    def test_multicast(self):
        """An odd first byte is multicast; broadcast counts too"""
        self.assertTrue(is_multicast("01:00:5e:00:00:fb"))
        self.assertTrue(is_multicast("33:33:00:00:00:01"))
        self.assertTrue(is_multicast("ff:ff:ff:ff:ff:ff"))
        self.assertFalse(is_multicast("3c:bd:c5:40:77:61"))
        self.assertFalse(is_multicast("da:47:5e:b3:f2:81"))

    def test_locally_administered(self):
        """Second hex digit 2, 6, a, or e is locally administered"""
        for mac in ["da:47:5e:b3:f2:81", "9a:c3:43:ad:95:e3", "d6:1b:bc:2d:ef:6f", "a6:ab:f1:8a:2f:9f", "02:00:00:00:00:01"]:
            self.assertTrue(is_locally_administered(mac), msg=mac)
        for mac in ["3c:bd:c5:40:77:61", "dc:46:28:a1:60:26", "00:00:5e:00:01:33"]:
            self.assertFalse(is_locally_administered(mac), msg=mac)


class Describe(unittest.TestCase):
    def test_vendors(self):
        """Universal unicast addresses are looked up by OUI"""
        self.assertEqual(describe("3c:bd:c5:40:77:61"), "Arcadyan")
        self.assertEqual(describe("3c:22:fb:45:a4:85"), "Apple")
        self.assertEqual(describe("DC-46-28-A1-60-26"), "Intel")
        self.assertEqual(describe("0:0:5e:0:1:33"), "IANA")

    def test_unknown_vendor(self):
        """A universal address with an OUI not in the table is unknown"""
        self.assertEqual(describe("00:11:22:33:44:55"), "unknown")

    def test_special_addresses(self):
        """Broadcast, multicast, and locally administered come before the vendor lookup"""
        self.assertEqual(describe("ff:ff:ff:ff:ff:ff"), "broadcast")
        self.assertEqual(describe("1:0:5e:0:0:fb"), "multicast")
        self.assertEqual(describe("da:47:5e:b3:f2:81"), "locally administered")

    def test_custom_vendor_table(self):
        """describe uses the vendors table it's given"""
        self.assertEqual(describe("00:11:22:33:44:55", {"00:11:22": "Cimsys"}), "Cimsys")
        self.assertEqual(describe("3c:bd:c5:40:77:61", {}), "unknown")

    def test_default_table_untouched(self):
        """The VENDORS table still has its entries"""
        self.assertEqual(VENDORS["3c:22:fb"], "Apple")


if __name__ == "__main__":
    unittest.main()
