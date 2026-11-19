import random
import unittest
from collections import Counter

from cluster import Cluster
from raft import RaftNode

SEEDS = range(8)
NEW_LEADER_WITHIN_MS = 1000


def elect(c, limit=2000):
    took = c.run_until(lambda: len(c.leaders()) == 1, limit)
    return took


class ElectionTest(unittest.TestCase):
    def test_elects_one_leader(self):
        """three nodes elect exactly one leader within a second"""
        for seed in SEEDS:
            c = Cluster(RaftNode, n=3, seed=seed)
            took = elect(c)
            self.assertIsNotNone(took, f"seed {seed}: no leader after 2 s; followers should start an election once their timer runs out")
            self.assertLessEqual(took, NEW_LEADER_WITHIN_MS, f"seed {seed}: the first election took {took} ms")
            leader = c.nodes[c.leaders()[0]]
            c.run(100)
            for nid, node in c.nodes.items():
                self.assertEqual(node.term, leader.term, f"seed {seed}: {nid} should learn the leader's term from its heartbeats")
                if nid != leader.id:
                    self.assertEqual(node.role, "follower", f"seed {seed}: {nid} should follow {leader.id}")

    def test_heartbeats_keep_the_leader(self):
        """a healthy leader keeps its job: no elections for 5 seconds"""
        for seed in SEEDS:
            c = Cluster(RaftNode, n=3, seed=seed)
            self.assertIsNotNone(elect(c), f"seed {seed}: no leader")
            leader = c.leaders()[0]
            term = c.nodes[leader].term
            c.run(5000)
            self.assertEqual(c.leaders(), [leader], f"seed {seed}: leadership changed with no failures; send heartbeats every HEARTBEAT_MS and reset followers' timers")
            self.assertEqual(c.nodes[leader].term, term, f"seed {seed}: the term went up from {term} to {c.nodes[leader].term} without any failure")

    def test_votes_once_per_term(self):
        """each node grants at most one vote per term"""
        for seed in SEEDS:
            c = Cluster(RaftNode, n=5, seed=seed, drop=0.2)
            c.run(4000)
            counts = Counter((voter, term) for voter, term, _ in c.votes_granted)
            twice = [(v, t) for (v, t), n in counts.items() if len({to for vv, tt, to in c.votes_granted if (vv, tt) == (v, t)}) > 1]
            self.assertEqual(twice, [], f"seed {seed}: these nodes voted for two candidates in the same term")

    def test_one_leader_per_term(self):
        """never two leaders in the same term, even with lost messages and crashes"""
        for seed in SEEDS:
            rng = random.Random(seed)
            c = Cluster(RaftNode, n=5, seed=seed, drop=0.15)
            for _ in range(6):
                c.run(rng.randint(300, 900))
                if c.leader() and rng.random() < 0.7:
                    victim = c.leader()
                    c.kill(victim)
                    c.run(rng.randint(200, 700))
                    c.revive(victim)
            self.assertEqual(c.violations, [], f"seed {seed}: two leaders were elected in one term: (time, term, first, second)")


class FailoverTest(unittest.TestCase):
    def test_new_leader_after_crash(self):
        """kills the leader at a random moment; the others elect a new one within a second"""
        for seed in SEEDS:
            rng = random.Random(100 + seed)
            c = Cluster(RaftNode, n=3, seed=seed)
            self.assertIsNotNone(elect(c), f"seed {seed}: no leader")
            c.run(rng.randint(50, 1000))
            old = c.leader()
            old_term = c.nodes[old].term
            c.kill(old)
            took = c.run_until(lambda: len(c.leaders()) == 1, 3000)
            self.assertIsNotNone(took, f"seed {seed}: no new leader after {old} died")
            self.assertLessEqual(took, NEW_LEADER_WITHIN_MS, f"seed {seed}: the new leader took {took} ms")
            new = c.leader()
            self.assertNotEqual(new, old)
            self.assertGreater(c.nodes[new].term, old_term, "a new leader is elected in a later term")

    def test_old_leader_steps_down(self):
        """a revived old leader learns of the new term and steps down"""
        for seed in SEEDS:
            c = Cluster(RaftNode, n=3, seed=seed)
            self.assertIsNotNone(elect(c), f"seed {seed}: no leader")
            old = c.leader()
            c.kill(old)
            self.assertIsNotNone(c.run_until(lambda: len(c.leaders()) == 1, 3000), f"seed {seed}: no new leader")
            new = c.leader()
            c.revive(old)  # it still believes it leads, in its old term
            took = c.run_until(lambda: c.nodes[old].role == "follower", 300)
            self.assertIsNotNone(took, f"seed {seed}: {old} kept acting as leader; step down on seeing a newer term")
            c.run(100)
            self.assertEqual(c.leaders(), [new])
            self.assertEqual(c.nodes[old].term, c.nodes[new].term)

    def test_minority_cannot_elect(self):
        """during a partition, only the side with a majority elects a leader"""
        for seed in SEEDS:
            c = Cluster(RaftNode, n=5, seed=seed)
            self.assertIsNotNone(elect(c), f"seed {seed}: no leader")
            old = c.leader()
            term = c.nodes[old].term
            minority = [old, next(p for p in c.ids if p != old)]
            majority = [p for p in c.ids if p not in minority]
            c.partition(minority, majority)
            took = c.run_until(lambda: len(c.leaders(majority)) == 1, 3000)
            self.assertIsNotNone(took, f"seed {seed}: the three-node side should elect a leader")
            c.run(2000)
            for nid in minority:
                node = c.nodes[nid]
                self.assertFalse(node.role == "leader" and node.term > term, f"seed {seed}: {nid} became leader in term {node.term} with only 2 of 5 votes")
            c.heal()
            c.run(500)
            self.assertEqual(len(c.leaders()), 1, f"seed {seed}: after healing there should be one leader, not {c.leaders()}")

            # Now cut two followers off together: they time out, but two of
            # five votes isn't a majority.
            leader = c.leader()
            term = c.nodes[leader].term
            cut = [p for p in c.ids if p != leader][:2]
            c.partition(cut, [p for p in c.ids if p not in cut])
            c.run(2000)
            for nid in cut:
                node = c.nodes[nid]
                self.assertNotEqual(node.role, "leader", f"seed {seed}: {nid} became leader in term {node.term} with only 2 of 5 votes; a majority of 5 is 3")
            self.assertEqual(c.leaders([p for p in c.ids if p not in cut]), [leader], f"seed {seed}: the majority side should keep its leader")
            self.assertEqual(c.nodes[leader].term, term)


if __name__ == "__main__":
    unittest.main()
