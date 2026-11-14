import unittest

from solution import (BARKER, WALL_LOSS_DB, best_channel, center_mhz, despread, fspl_db, hop_sequence, jammed_fraction,
                      overlaps, received_dbm, spread, usage_tier)


class Channels(unittest.TestCase):
    def test_centers(self):
        """Channel 1 is 2412 MHz, 6 is 2437, 11 is 2462"""
        self.assertEqual(center_mhz(1), 2412)
        self.assertEqual(center_mhz(6), 2437)
        self.assertEqual(center_mhz(11), 2462)
        self.assertEqual(center_mhz(13), 2472)

    def test_channel_14(self):
        """Channel 14 is the odd one out, at 2484 MHz"""
        self.assertEqual(center_mhz(14), 2484)

    def test_no_such_channel(self):
        """Only channels 1 to 14 exist"""
        for bad in [0, 15, -1, 36]:
            with self.assertRaises(ValueError):
                center_mhz(bad)

    def test_one_six_eleven(self):
        """1, 6, and 11 don't overlap each other"""
        self.assertFalse(overlaps(1, 6))
        self.assertFalse(overlaps(6, 11))
        self.assertFalse(overlaps(1, 11))

    def test_neighbors_overlap(self):
        """Channels less than 22 MHz apart overlap, including the same channel"""
        self.assertTrue(overlaps(1, 3))
        self.assertTrue(overlaps(1, 5))
        self.assertTrue(overlaps(6, 6))
        self.assertTrue(overlaps(7, 6))
        self.assertTrue(overlaps(13, 14))

    def test_overlaps_checks_channels(self):
        """Bad channels raise ValueError"""
        with self.assertRaises(ValueError):
            overlaps(1, 20)


class BestChannel(unittest.TestCase):
    def test_empty_air(self):
        """Nobody nearby: channel 1"""
        self.assertEqual(best_channel([]), 1)

    def test_avoids_busy(self):
        """Two neighbors on 1 and one on 6: pick 11"""
        self.assertEqual(best_channel([1, 1, 6]), 11)

    def test_drill(self):
        """A neighbor on 6: 1 is clear, and wins the tie with 11"""
        self.assertEqual(best_channel([6]), 1)

    def test_counts_overlap_not_just_equal(self):
        """Neighbors on 2 and 3 overlap both 1 and 6"""
        self.assertEqual(best_channel([2, 3, 11]), 11)

    def test_tie_goes_to_first(self):
        """One on each of 1, 6, and 11: channel 1"""
        self.assertEqual(best_channel([6, 11, 1]), 1)


class PathLoss(unittest.TestCase):
    def test_ten_meters(self):
        """10 m on channel 6 loses about 60.19 dB"""
        self.assertAlmostEqual(fspl_db(10, 2437), 60.187, places=2)

    def test_five_ghz_loses_more(self):
        """The same 10 m at 5180 MHz loses about 66.74 dB"""
        self.assertAlmostEqual(fspl_db(10, 5180), 66.737, places=2)

    def test_double_distance(self):
        """Twice the distance costs about 6 dB more"""
        self.assertAlmostEqual(fspl_db(20, 2437) - fspl_db(10, 2437), 6.0206, places=3)

    def test_bad_values(self):
        """Distance and frequency must be positive"""
        for d, f in [(0, 2437), (-1, 2437), (10, 0)]:
            with self.assertRaises(ValueError):
                fspl_db(d, f)

    def test_received_no_walls(self):
        """20 dBm out, 10 m on channel 6: about -40.19 dBm"""
        self.assertAlmostEqual(received_dbm(20, 10, 2437), -40.187, places=2)

    def test_received_with_walls(self):
        """Drywall and concrete add 3 + 12 dB"""
        self.assertAlmostEqual(received_dbm(20, 10, 2437, ["drywall", "concrete"]), -55.187, places=2)

    def test_wall_table(self):
        """The reading's rough values"""
        self.assertEqual(WALL_LOSS_DB, {"drywall": 3, "glass": 4, "brick": 8, "concrete": 12, "metal": 20})

    def test_unknown_material(self):
        """Materials not in the table raise ValueError"""
        with self.assertRaises(ValueError):
            received_dbm(20, 10, 2437, ["cheese"])


class Dsss(unittest.TestCase):
    def test_one_bit(self):
        """A 1 is the Barker code"""
        self.assertEqual(spread([1]), BARKER)

    def test_zero_bit(self):
        """A 0 is the Barker code inverted"""
        self.assertEqual(spread([0]), [0, 1, 0, 0, 1, 0, 0, 0, 1, 1, 1])

    def test_eleven_chips_per_bit(self):
        """Four bits become 44 chips"""
        self.assertEqual(len(spread([1, 0, 0, 1])), 44)

    def test_bad_bit(self):
        """Only 0 and 1"""
        with self.assertRaises(ValueError):
            spread([1, 2])

    def test_round_trip(self):
        """despread undoes spread"""
        bits = [1, 0, 1, 1, 0, 0, 1, 0]
        self.assertEqual(despread(spread(bits)), bits)

    def test_survives_noise(self):
        """Up to 5 flipped chips per bit still decode"""
        chips = spread([1, 0, 1])
        for i in [0, 3, 5, 7, 9, 11, 12, 13, 14, 15, 22]:
            chips[i] ^= 1
        self.assertEqual(despread(chips), [1, 0, 1])

    def test_too_much_noise(self):
        """Six flipped chips out of 11 turn a 1 into a 0"""
        chips = spread([1])
        for i in range(6):
            chips[i] ^= 1
        self.assertEqual(despread(chips), [0])

    def test_bad_length(self):
        """Chip counts must be a multiple of 11"""
        with self.assertRaises(ValueError):
            despread([1, 0, 1])

    def test_empty(self):
        """No chips, no bits"""
        self.assertEqual(despread([]), [])
        self.assertEqual(spread([]), [])


class Hopping(unittest.TestCase):
    def test_example(self):
        """Seed 42 starts 50, 32, 27, 71, 57"""
        self.assertEqual(hop_sequence(42, 5), [50, 32, 27, 71, 57])

    def test_both_ends_agree(self):
        """The same seed gives the same sequence"""
        self.assertEqual(hop_sequence(1234, 50), hop_sequence(1234, 50))

    def test_different_seeds(self):
        """A different seed gives a different sequence"""
        self.assertNotEqual(hop_sequence(1, 20), hop_sequence(2, 20))

    def test_channel_count(self):
        """Seed 42 over 10 channels: 7, 4, 3, 6, 5"""
        self.assertEqual(hop_sequence(42, 5, channels=10), [7, 4, 3, 6, 5])

    def test_in_range(self):
        """Every hop is a valid channel"""
        self.assertTrue(all(0 <= c < 79 for c in hop_sequence(99, 500)))

    def test_zero_hops(self):
        """Zero hops is an empty list"""
        self.assertEqual(hop_sequence(5, 0), [])

    def test_bad_values(self):
        """Negative hops or no channels"""
        with self.assertRaises(ValueError):
            hop_sequence(1, -1)
        with self.assertRaises(ValueError):
            hop_sequence(1, 5, channels=0)

    def test_jammer(self):
        """One jammed channel hits only about 1 hop in 100 here"""
        self.assertAlmostEqual(jammed_fraction(hop_sequence(1, 1000), [0]), 0.01)

    def test_jammer_simple(self):
        """Two of four hops land on jammed channels"""
        self.assertAlmostEqual(jammed_fraction([3, 7, 3, 9], [3]), 0.5)
        self.assertAlmostEqual(jammed_fraction([3, 7, 3, 9], []), 0.0)

    def test_jammer_empty(self):
        """An empty sequence raises ValueError"""
        with self.assertRaises(ValueError):
            jammed_fraction([], [1])


class Usage(unittest.TestCase):
    def test_tiers(self):
        """Light up to 25, medium up to 300, heavy above"""
        self.assertEqual(usage_tier(10), "light")
        self.assertEqual(usage_tier(25), "light")
        self.assertEqual(usage_tier(26), "medium")
        self.assertEqual(usage_tier(300), "medium")
        self.assertEqual(usage_tier(301), "heavy")
        self.assertEqual(usage_tier(800), "heavy")

    def test_zero(self):
        """Zero is light"""
        self.assertEqual(usage_tier(0), "light")

    def test_negative(self):
        """Negative bandwidth raises ValueError"""
        with self.assertRaises(ValueError):
            usage_tier(-5)


if __name__ == "__main__":
    unittest.main()
