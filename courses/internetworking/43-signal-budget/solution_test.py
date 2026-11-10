import unittest

from solution import (
    MEDIA,
    choose_medium,
    db_loss,
    max_segment,
    power_after,
    repeaters_needed,
    transfer_seconds,
)


class DbLoss(unittest.TestCase):
    def test_half_power_is_about_3_db(self):
        """Losing half the power is about 3 dB"""
        self.assertAlmostEqual(db_loss(100, 50), 3.0103, places=3)

    def test_tenth_and_hundredth(self):
        """A tenth of the power is 10 dB, a hundredth is 20 dB"""
        self.assertAlmostEqual(db_loss(10, 1), 10.0)
        self.assertAlmostEqual(db_loss(5, 0.05), 20.0)

    def test_no_loss(self):
        """The same power in and out is 0 dB"""
        self.assertAlmostEqual(db_loss(7, 7), 0.0)

    def test_rejects_non_positive_power(self):
        """Zero or negative power raises ValueError"""
        for args in [(0, 1), (1, 0), (-5, 1), (1, -5)]:
            with self.assertRaises(ValueError, msg=f"db_loss{args}"):
                db_loss(*args)


class PowerAfter(unittest.TestCase):
    def test_20_db_leaves_a_hundredth(self):
        """100 m of 20 dB/100 m cable leaves a hundredth of the power"""
        self.assertAlmostEqual(power_after(100, 20, 100), 1.0)

    def test_loss_scales_with_length(self):
        """50 m of 10 dB/100 m cable loses 5 dB"""
        self.assertAlmostEqual(power_after(1, 10, 50), 10 ** -0.5)

    def test_zero_length(self):
        """No cable, no loss"""
        self.assertAlmostEqual(power_after(42, 20, 0), 42)


class MaxSegment(unittest.TestCase):
    def test_basic(self):
        """20 dB of headroom on 20 dB/100 m cable reaches 100 m"""
        self.assertAlmostEqual(max_segment(100, 1, 20), 100.0)

    def test_longer_run(self):
        """30 dB of headroom on 6 dB/100 m cable reaches 500 m"""
        self.assertAlmostEqual(max_segment(10, 0.01, 6), 500.0)

    def test_round_trip_with_power_after(self):
        """At exactly max_segment meters, the power left is min_power"""
        length = max_segment(50, 2, 7.5)
        self.assertAlmostEqual(power_after(50, 7.5, length), 2)

    def test_too_weak_to_start(self):
        """If the signal starts below min_power, it can't go anywhere"""
        self.assertEqual(max_segment(1, 5, 10), 0.0)
        self.assertEqual(max_segment(5, 5, 10), 0.0)

    def test_rejects_bad_attenuation(self):
        """Zero or negative attenuation raises ValueError"""
        with self.assertRaises(ValueError):
            max_segment(100, 1, 0)
        with self.assertRaises(ValueError):
            max_segment(100, 1, -3)


class Repeaters(unittest.TestCase):
    def test_fits_in_one_segment(self):
        """A run no longer than one segment needs no repeaters"""
        self.assertEqual(repeaters_needed(100, 100), 0)
        self.assertEqual(repeaters_needed(30, 100), 0)
        self.assertEqual(repeaters_needed(0, 100), 0)

    def test_just_over(self):
        """101 m with 100 m segments needs one repeater"""
        self.assertEqual(repeaters_needed(101, 100), 1)

    def test_several(self):
        """250 m needs 2 repeaters, 1000 m needs 9"""
        self.assertEqual(repeaters_needed(250, 100), 2)
        self.assertEqual(repeaters_needed(1000, 100), 9)

    def test_rejects_bad_segment(self):
        """A zero or negative segment length raises ValueError"""
        with self.assertRaises(ValueError):
            repeaters_needed(100, 0)


class TransferSeconds(unittest.TestCase):
    def test_gigabit(self):
        """125,000,000 bytes over 1000 Mbps takes 1 second"""
        self.assertAlmostEqual(transfer_seconds(125_000_000, 1000), 1.0)

    def test_bits_vs_bytes(self):
        """1,000,000 bytes is 8,000,000 bits: 1 second at 8 Mbps"""
        self.assertAlmostEqual(transfer_seconds(1_000_000, 8), 1.0)

    def test_slow_link(self):
        """A 5 MB file over 10 Mbps takes 4 seconds"""
        self.assertAlmostEqual(transfer_seconds(5_000_000, 10), 4.0)


class ChooseMedium(unittest.TestCase):
    def test_cheapest_for_a_desk(self):
        """A quiet 80 m run at 500 Mbps: plain UTP is cheapest"""
        self.assertEqual(choose_medium(MEDIA, 80, 500, False), "UTP Cat 6")

    def test_noisy_rules_out_utp(self):
        """The same run in a noisy factory can't use UTP"""
        self.assertEqual(choose_medium(MEDIA, 80, 500, True), "Broadband coax")

    def test_needs_more_bandwidth(self):
        """80 m at 5 Gbps needs STP or fiber, and STP is cheaper"""
        self.assertEqual(choose_medium(MEDIA, 80, 5000, False), "STP Cat 6a")

    def test_distance_rules_out_copper_pairs(self):
        """300 m is too far for twisted pair"""
        self.assertEqual(choose_medium(MEDIA, 300, 1000, False), "Broadband coax")
        self.assertEqual(choose_medium(MEDIA, 300, 5000, False), "Multimode fiber")

    def test_between_buildings(self):
        """2 km between buildings needs single-mode fiber"""
        self.assertEqual(choose_medium(MEDIA, 2000, 100, False), "Single-mode fiber")

    def test_exactly_the_segment_limit(self):
        """A run exactly as long as the segment limit still fits"""
        self.assertEqual(choose_medium(MEDIA, 100, 100, False), "UTP Cat 6")

    def test_nothing_fits(self):
        """20 km in one segment is too far for anything in the catalog"""
        self.assertIsNone(choose_medium(MEDIA, 20000, 1, False))

    def test_tie_goes_to_first(self):
        """When two media cost the same, the first one listed wins"""
        media = [
            {"name": "A", "max_segment_m": 100, "mbps": 100, "emi_resistant": True, "cost_per_m": 1.0},
            {"name": "B", "max_segment_m": 100, "mbps": 100, "emi_resistant": True, "cost_per_m": 1.0},
        ]
        self.assertEqual(choose_medium(media, 50, 100, True), "A")

    def test_empty_catalog(self):
        """An empty catalog has nothing to offer"""
        self.assertIsNone(choose_medium([], 10, 1, False))


if __name__ == "__main__":
    unittest.main()
