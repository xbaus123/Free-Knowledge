import unittest

from solution import (META_STATES, availability, check_reading, downtime_minutes, parallel, parity, raid_tolerates,
                      raid_usable, rebuild, series)


class Availability(unittest.TestCase):
    def test_reading_example(self):
        """MTBF 99, MTTR 1 gives 99%"""
        self.assertAlmostEqual(availability(99, 1), 0.99)

    def test_drill_router(self):
        """MTBF 999, MTTR 1 gives three nines"""
        self.assertAlmostEqual(availability(999, 1), 0.999)

    def test_no_repair_time(self):
        """No repair time means always available"""
        self.assertAlmostEqual(availability(500, 0), 1.0)

    def test_bad_values(self):
        """MTBF must be positive, MTTR not negative"""
        for mtbf, mttr in [(0, 1), (-5, 1), (10, -1)]:
            with self.assertRaises(ValueError):
                availability(mtbf, mttr)


class Downtime(unittest.TestCase):
    def test_three_nines(self):
        """99.9% allows about 525.6 minutes (8.76 hours) a year"""
        self.assertAlmostEqual(downtime_minutes(0.999), 525.6, places=3)

    def test_four_and_five_nines(self):
        """About 52.56 and 5.256 minutes"""
        self.assertAlmostEqual(downtime_minutes(0.9999), 52.56, places=3)
        self.assertAlmostEqual(downtime_minutes(0.99999), 5.256, places=3)

    def test_other_period(self):
        """99% over 30 days is 432 minutes"""
        self.assertAlmostEqual(downtime_minutes(0.99, days=30), 432.0, places=3)

    def test_out_of_range(self):
        """Availability must be between 0 and 1"""
        for bad in [-0.1, 1.5, 99.9]:
            with self.assertRaises(ValueError):
                downtime_minutes(bad)


class SeriesParallel(unittest.TestCase):
    def test_series_reading(self):
        """Firewall then web server, both 99%: 98.01%"""
        self.assertAlmostEqual(series([0.99, 0.99]), 0.9801)

    def test_series_drill(self):
        """Three 90% parts in series: 72.9%"""
        self.assertAlmostEqual(series([0.9, 0.9, 0.9]), 0.729)

    def test_parallel_reading(self):
        """Two 99% web servers in parallel: 99.99%"""
        self.assertAlmostEqual(parallel([0.99, 0.99]), 0.9999)

    def test_parallel_drill(self):
        """Three 90% parts in parallel: 99.9%"""
        self.assertAlmostEqual(parallel([0.9, 0.9, 0.9]), 0.999)

    def test_single_part(self):
        """One part is just itself, either way"""
        self.assertAlmostEqual(series([0.95]), 0.95)
        self.assertAlmostEqual(parallel([0.95]), 0.95)

    def test_empty(self):
        """No parts is an error"""
        for f in (series, parallel):
            with self.assertRaises(ValueError):
                f([])


class Raid(unittest.TestCase):
    def test_raid5_check(self):
        """Four 2 TB drives in RAID 5: 6 TB, one can fail"""
        self.assertEqual(raid_usable(5, 4, 2), 6)
        self.assertEqual(raid_tolerates(5, 4), 1)

    def test_raid5_review(self):
        """Five 4 TB drives in RAID 5: 16 TB"""
        self.assertEqual(raid_usable(5, 5, 4), 16)

    def test_raid1(self):
        """RAID 1 mirrors: one drive's worth, all but one can fail"""
        self.assertEqual(raid_usable(1, 2, 4), 4)
        self.assertEqual(raid_usable(1, 3, 4), 4)
        self.assertEqual(raid_tolerates(1, 3), 2)

    def test_raid0(self):
        """RAID 0: all the space, no redundancy"""
        self.assertEqual(raid_usable(0, 3, 2), 6)
        self.assertEqual(raid_tolerates(0, 3), 0)

    def test_raid6(self):
        """RAID 6: all but two drives, two can fail"""
        self.assertEqual(raid_usable(6, 6, 3), 12)
        self.assertEqual(raid_tolerates(6, 6), 2)

    def test_too_few_drives(self):
        """Each level has a minimum"""
        for level, drives in [(0, 1), (1, 1), (5, 2), (6, 3)]:
            with self.assertRaises(ValueError):
                raid_usable(level, drives, 1)
            with self.assertRaises(ValueError):
                raid_tolerates(level, drives)

    def test_unknown_level(self):
        """Only 0, 1, 5, and 6"""
        for level in [2, 3, 4, 7, 10]:
            with self.assertRaises(ValueError):
                raid_usable(level, 8, 1)


class Parity(unittest.TestCase):
    def test_two_blocks(self):
        """0x0f XOR 0xf0 is 0xff"""
        self.assertEqual(parity([b"\x0f", b"\xf0"]), b"\xff")

    def test_same_blocks_cancel(self):
        """A block XOR itself is all zeros"""
        self.assertEqual(parity([b"abc", b"abc"]), b"\x00\x00\x00")

    def test_one_block(self):
        """One block's parity is the block itself (a mirror)"""
        self.assertEqual(parity([b"web"]), b"web")

    def test_three_blocks(self):
        """Byte by byte across three blocks"""
        self.assertEqual(parity([b"\x01\x02", b"\x04\x08", b"\x10\x20"]), b"\x15\x2a")

    def test_bad_blocks(self):
        """No blocks, or different lengths"""
        with self.assertRaises(ValueError):
            parity([])
        with self.assertRaises(ValueError):
            parity([b"ab", b"abc"])


class Rebuild(unittest.TestCase):
    def test_starter_example(self):
        """Lose the middle drive and get it back"""
        data = [b"web", b"app", b"db!"]
        self.assertEqual(rebuild([b"web", None, b"db!"], parity(data)), b"app")

    def test_every_position(self):
        """Any one drive can be rebuilt"""
        data = [b"\x10\x20\x30\x40", b"\xaa\xbb\xcc\xdd", b"\x01\x02\x03\x04", b"\xff\x00\xff\x00"]
        p = parity(data)
        for i in range(len(data)):
            blocks = list(data)
            blocks[i] = None
            self.assertEqual(rebuild(blocks, p), data[i])

    def test_docstring_example(self):
        """rebuild([0x0f, None], 0xff) is 0xf0"""
        self.assertEqual(rebuild([b"\x0f", None], b"\xff"), b"\xf0")

    def test_wrong_number_missing(self):
        """Nothing missing, or two drives lost: RAID 5 can't help"""
        with self.assertRaises(ValueError):
            rebuild([b"a", b"b"], b"\x03")
        with self.assertRaises(ValueError):
            rebuild([None, None, b"c"], b"\x00")


class CheckReading(unittest.TestCase):
    CPU = {"idle": (1, 5), "normal": (20, 50), "busy": (60, 90)}

    def test_drill(self):
        """The drill's readings"""
        self.assertEqual(check_reading(3, "idle", self.CPU), "ok")
        self.assertEqual(check_reading(70, "idle", self.CPU), "high")
        self.assertEqual(check_reading(35, "normal", self.CPU), "ok")
        self.assertEqual(check_reading(40, "busy", self.CPU), "low")

    def test_edges_inclusive(self):
        """The ends of each range are ok"""
        self.assertEqual(check_reading(90, "busy", self.CPU), "ok")
        self.assertEqual(check_reading(60, "busy", self.CPU), "ok")
        self.assertEqual(check_reading(1, "idle", self.CPU), "ok")
        self.assertEqual(check_reading(0, "idle", self.CPU), "low")

    def test_six_states(self):
        """META_STATES lists the six meta-states in order"""
        self.assertEqual(META_STATES, ["start-up", "idle", "normal", "busy", "failing", "failed"])

    def test_unknown_state(self):
        """Not one of the six"""
        with self.assertRaises(ValueError):
            check_reading(10, "sleepy", self.CPU)

    def test_no_baseline(self):
        """A real meta-state with no range given"""
        with self.assertRaises(ValueError):
            check_reading(10, "failing", self.CPU)


if __name__ == "__main__":
    unittest.main()
