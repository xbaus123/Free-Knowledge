import random
import unittest

from solution import CausalReader, Clock, Follower, Leader, Session, lag_report


def cluster(*lags):
    clock = Clock()
    leader = Leader(clock)
    followers = [Follower(f"f{i + 1}", leader, lag) for i, lag in enumerate(lags)]
    return clock, leader, followers


class LagReportTest(unittest.TestCase):
    def test_caught_up(self):
        """reports zero lag for followers that have everything"""
        clock, leader, fs = cluster(0.05, 0.05)
        leader.write("a", 1)
        clock.advance(1)
        self.assertEqual(lag_report(leader, fs), {"f1": (0, 0.0), "f2": (0, 0.0)})
        self.assertEqual(lag_report(Leader(Clock()), []), {})

    def test_behind(self):
        """counts writes behind, and seconds since the oldest unapplied write"""
        clock, leader, fs = cluster(0.5, 5.0)
        leader.write("a", 1)  # t = 0
        clock.advance(1)
        leader.write("b", 2)  # t = 1
        clock.advance(0.25)
        leader.write("c", 3)  # t = 1.25
        clock.advance(0.4)  # t = 1.65
        report = lag_report(leader, fs)
        self.assertEqual(report["f1"][0], 1)
        self.assertAlmostEqual(report["f1"][1], 0.4, msg="c committed at 1.25 and hasn't arrived")
        self.assertEqual(report["f2"][0], 3)
        self.assertAlmostEqual(report["f2"][1], 1.65)

    def test_quiet_leader(self):
        """shows how a quiet leader hides lag measured in writes"""
        clock, leader, fs = cluster(60.0)
        leader.write("a", 1)
        clock.advance(30)
        behind, seconds = lag_report(leader, fs)["f1"]
        self.assertEqual(behind, 1)
        self.assertAlmostEqual(seconds, 30.0, msg="only one write behind, but 30 seconds stale")


class ReadYourWritesTest(unittest.TestCase):
    def test_anomaly_without(self):
        """without the guarantee, a user can miss their own write"""
        clock, leader, fs = cluster(0.05)
        s = Session(leader, fs)
        s.write("profile", "new photo")
        clock.advance(0.03)
        self.assertIsNone(s.read("profile"), "the follower is 50 ms behind")
        self.assertEqual(leader.reads, 0, "plain reads always go to followers")

    def test_sees_own_write(self):
        """reads from the leader until a follower has the user's write"""
        clock, leader, fs = cluster(0.05, 0.05)
        s = Session(leader, fs, read_your_writes=True)
        s.write("profile", "new photo")
        clock.advance(0.03)
        self.assertEqual(s.read("profile"), "new photo")
        self.assertEqual(leader.reads, 1)
        clock.advance(0.05)
        self.assertEqual(s.read("profile"), "new photo")
        self.assertEqual(leader.reads, 1, "a caught-up follower is good enough")

    def test_prefers_caught_up_follower(self):
        """uses any follower that's caught up, before the leader"""
        clock, leader, fs = cluster(5.0, 0.01)
        s = Session(leader, fs, read_your_writes=True)
        s.write("k", "v")
        clock.advance(0.02)
        for _ in range(4):
            self.assertEqual(s.read("k"), "v")
        self.assertEqual((leader.reads, fs[0].reads, fs[1].reads), (0, 0, 4))

    def test_only_own_writes(self):
        """doesn't wait for other users' writes"""
        clock, leader, fs = cluster(0.05)
        alice = Session(leader, fs, read_your_writes=True)
        bob = Session(leader, fs, read_your_writes=True)
        alice.write("a", 1)
        clock.advance(0.01)
        self.assertIsNone(bob.read("a"), "Bob hasn't written anything, so a stale read is allowed")
        self.assertEqual(leader.reads, 0)

    def test_round_robin(self):
        """rotates through the followers"""
        clock, leader, fs = cluster(0.0, 0.0, 0.0)
        s = Session(leader, fs)
        for _ in range(6):
            s.read("x")
        self.assertEqual([f.reads for f in fs], [2, 2, 2])


class MonotonicReadsTest(unittest.TestCase):
    def setup(self, **guarantees):
        clock, leader, fs = cluster(0.01, 1.0)  # one fast follower, one slow
        s = Session(leader, fs, **guarantees)
        leader.write("comment", "first!")
        clock.advance(0.5)
        return clock, leader, fs, s

    def test_anomaly_without(self):
        """without the guarantee, time can go backward"""
        clock, leader, fs, s = self.setup()
        self.assertEqual([s.read("comment"), s.read("comment")], ["first!", None])

    def test_never_goes_back(self):
        """never reads an older state than the session has seen"""
        clock, leader, fs, s = self.setup(monotonic_reads=True)
        self.assertEqual([s.read("comment") for _ in range(4)], ["first!"] * 4)
        self.assertEqual(fs[1].reads, 0, "the slow follower is behind what this session saw")
        self.assertEqual(leader.reads, 0)
        clock.advance(1)
        self.assertEqual(s.read("comment"), "first!")
        self.assertEqual(s.read("comment"), "first!")
        self.assertEqual(fs[1].reads, 1, "once it catches up it's usable again")

    def test_leader_reads_count(self):
        """counts a read from the leader as state the session has seen"""
        clock, leader, fs = cluster(1.0, 1.0)
        s = Session(leader, fs, read_your_writes=True, monotonic_reads=True)
        other = Session(leader, fs)
        s.write("a", 1)
        other.write("b", 2)  # LSN 2, written by someone else
        self.assertEqual(s.read("b"), 2, "read from the leader at LSN 2")
        clock.advance(1.5)
        self.assertEqual(s.read("b"), 2)
        self.assertEqual(leader.reads, 1)

    def test_random_workload(self):
        """never shows any key going back in time"""
        rng = random.Random(11)
        clock, leader, fs = cluster(0.0, 0.2, 0.7, 1.5)
        writer = Session(leader, fs)
        s = Session(leader, fs, read_your_writes=True, monotonic_reads=True)
        newest = {}
        for i in range(400):
            key = rng.choice("abc")
            if rng.random() < 0.3:
                writer.write(key, i)
            if rng.random() < 0.1:
                s.write(key, i)
                newest[key] = i
            value = s.read(key)
            if value is not None:
                self.assertGreaterEqual(value, newest.get(key, -1), f"step {i}")
                newest[key] = value
            clock.advance(rng.uniform(0, 0.1))
        self.assertLess(leader.reads, 100, "most reads should still go to followers")


class ConsistentPrefixTest(unittest.TestCase):
    QUESTION = {"id": "q", "deps": [], "text": "Does anyone know when the store closes?"}
    ANSWER = {"id": "a", "deps": ["q"], "text": "At 9 tonight."}

    def test_in_order(self):
        """shows writes that arrive in order at once"""
        r = CausalReader()
        r.receive(self.QUESTION)
        r.receive(self.ANSWER)
        self.assertEqual(r.visible, ["q", "a"])
        self.assertEqual(r.pending(), [])

    def test_holds_effects(self):
        """holds an answer that arrives before its question"""
        r = CausalReader()
        r.receive(self.ANSWER)  # its partition replicated faster
        self.assertEqual(r.visible, [])
        self.assertEqual(r.pending(), ["a"])
        r.receive(self.QUESTION)
        self.assertEqual(r.visible, ["q", "a"])
        self.assertEqual(r.pending(), [])

    def test_chains(self):
        """releases a whole chain once its first write arrives"""
        r = CausalReader()
        for w in [
            {"id": "c", "deps": ["b"]},
            {"id": "x", "deps": []},
            {"id": "d", "deps": ["c", "x"]},
            {"id": "b", "deps": ["a"]},
        ]:
            r.receive(w)
        self.assertEqual(r.visible, ["x"])
        self.assertEqual(r.pending(), ["c", "d", "b"])
        r.receive({"id": "a", "deps": []})
        self.assertEqual(r.visible, ["x", "a", "b", "c", "d"])

    def test_duplicates(self):
        """ignores a write delivered twice"""
        r = CausalReader()
        r.receive(self.ANSWER)
        r.receive(self.ANSWER)
        r.receive(self.QUESTION)
        r.receive(self.QUESTION)
        r.receive(self.ANSWER)
        self.assertEqual(r.visible, ["q", "a"])

    def test_random_order(self):
        """respects every dependency, whatever the arrival order"""
        rng = random.Random(5)
        writes = []
        for i in range(60):
            deps = rng.sample(range(i), min(i, rng.randint(0, 2)))
            writes.append({"id": i, "deps": deps})
        arrival = writes[:]
        rng.shuffle(arrival)
        r = CausalReader()
        for w in arrival:
            r.receive(w)
        self.assertEqual(sorted(r.visible), list(range(60)))
        position = {w: i for i, w in enumerate(r.visible)}
        for w in writes:
            for d in w["deps"]:
                self.assertLess(position[d], position[w["id"]])


if __name__ == "__main__":
    unittest.main()
