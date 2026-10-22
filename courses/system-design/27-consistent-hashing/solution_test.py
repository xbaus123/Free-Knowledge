import os
import subprocess
import sys
import time
import unittest
from collections import Counter

from solution import Partitioner

KEYS = [f"user:{i}" for i in range(10_000)]
NODES = [f"node-{i}" for i in range(10)]


def assignments(p):
    return {k: p.node_for(k) for k in KEYS}


class PartitionerTest(unittest.TestCase):
    def test_assigns_every_key(self):
        """sends every key to one of the nodes, the same one each time"""
        p = Partitioner(NODES)
        for k in KEYS[:500]:
            self.assertIn(p.node_for(k), NODES)
            self.assertEqual(p.node_for(k), p.node_for(k))

    def test_even_distribution(self):
        """spreads 10,000 keys evenly over 10 nodes"""
        counts = Counter(assignments(Partitioner(NODES)).values())
        mean = len(KEYS) / len(NODES)
        self.assertEqual(set(counts), set(NODES), "every node should get keys")
        self.assertLessEqual(max(counts.values()), 1.25 * mean, f"busiest node has {max(counts.values())} keys (mean {mean:.0f}); use more virtual nodes")
        self.assertGreaterEqual(min(counts.values()), 0.75 * mean, f"quietest node has {min(counts.values())} keys (mean {mean:.0f}); use more virtual nodes")

    def test_adding_a_node_moves_few_keys(self):
        """moves at most 1/N of the keys when an 11th node joins, all to the new node"""
        p = Partitioner(NODES)
        before = assignments(p)
        p.add_node("node-10")
        after = assignments(p)
        moved = [k for k in KEYS if before[k] != after[k]]
        limit = len(KEYS) // len(NODES)
        self.assertLessEqual(len(moved), limit, f"{len(moved)} of {len(KEYS)} keys moved; at most {limit} (1/N) may move")
        self.assertTrue(all(after[k] == "node-10" for k in moved), "keys should only move to the new node")
        self.assertGreater(len(moved), len(KEYS) // 20, "the new node should take its share of keys")

    def test_removing_a_node_spreads_its_keys(self):
        """moves only the removed node's keys, spread across the others"""
        p = Partitioner(NODES)
        before = assignments(p)
        p.remove_node("node-3")
        after = assignments(p)
        moved = [k for k in KEYS if before[k] != after[k]]
        wrong = [k for k in moved if before[k] != "node-3"]
        self.assertEqual(len(wrong), 0, f"{len(wrong)} keys moved that weren't on node-3 (for example {wrong[:3]}); only node-3's keys should move")
        self.assertTrue(all(after[k] != "node-3" for k in KEYS), "no key should map to a removed node")
        receivers = Counter(after[k] for k in moved)
        self.assertLessEqual(max(receivers.values()), 0.3 * len(moved), "one node absorbed most of the load; virtual nodes spread it out")
        p.add_node("node-3")
        self.assertEqual(assignments(p), before, "adding the node back should restore the original placement")

    def test_same_answer_in_every_process(self):
        """places keys the same way in every process"""
        script = "import solution, json; p = solution.Partitioner(%r); print(json.dumps([p.node_for(k) for k in %r]))" % (NODES, KEYS[:200])
        outs = []
        for seed in ("1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            r = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, env=env, cwd=os.path.dirname(os.path.abspath(__file__)))
            self.assertEqual(r.returncode, 0, r.stderr)
            outs.append(r.stdout)
        self.assertEqual(outs[0], outs[1], "Python's hash() changes between processes; use a stable hash like md5")

    def test_lookups_are_fast(self):
        """finds a key's node by binary search, not by scanning the ring"""
        p = Partitioner([f"node-{i}" for i in range(50)])
        start = time.perf_counter()
        for k in KEYS:
            p.node_for(k)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 1.5, f"10,000 lookups took {elapsed:.2f} s; use bisect on a sorted ring")


if __name__ == "__main__":
    unittest.main()
