import unittest
from collections import defaultdict

from solution import ConsumerGroup, TaskQueue, Topic, stable_hash


class TaskQueueTest(unittest.TestCase):
    def test_delivers_in_order(self):
        """delivers the oldest visible message first"""
        q = TaskQueue()
        for body in ("resize photo 1", "resize photo 2", "send email"):
            q.send(body)
        got = [q.receive(now=0) for _ in range(3)]
        self.assertEqual([m[1] for m in got], ["resize photo 1", "resize photo 2", "send email"])
        self.assertEqual(len({m[0] for m in got}), 3, "message ids are unique")
        self.assertIsNone(q.receive(now=0), "delivered messages are hidden from other consumers")

    def test_ack_deletes(self):
        """deletes a message once it's acknowledged"""
        q = TaskQueue(visibility_timeout=30)
        q.send("job")
        _, _, receipt = q.receive(now=0)
        self.assertTrue(q.ack(receipt))
        self.assertIsNone(q.receive(now=100), "an acknowledged message never comes back")
        self.assertFalse(q.ack(receipt), "it's already gone")

    def test_redelivers_after_timeout(self):
        """redelivers a message whose consumer didn't acknowledge in time"""
        q = TaskQueue(visibility_timeout=30)
        q.send("charge card")
        id1, _, slow_receipt = q.receive(now=0)
        self.assertIsNone(q.receive(now=29))
        id2, body, fresh_receipt = q.receive(now=30)
        self.assertEqual((id2, body), (id1, "charge card"), "at-least-once: the same message, again")
        self.assertNotEqual(slow_receipt, fresh_receipt)
        self.assertFalse(q.ack(slow_receipt), "the first consumer lost the message when its timeout ran out")
        self.assertTrue(q.ack(fresh_receipt))

    def test_nack(self):
        """makes a negatively acknowledged message visible right away"""
        q = TaskQueue(visibility_timeout=30)
        q.send("a")
        q.send("b")
        _, _, receipt = q.receive(now=0)
        self.assertTrue(q.nack(receipt, now=5))
        self.assertEqual(q.receive(now=5)[1], "a", "it keeps its place at the front")
        self.assertFalse(q.nack(receipt, now=6), "a stale receipt can't give it back")

    def test_dead_letters(self):
        """moves a message that keeps failing to the dead-letter queue"""
        q = TaskQueue(visibility_timeout=10, max_receives=3)
        q.send("poison")
        q.send("fine")
        now = 0
        for attempt in range(3):
            _, body, receipt = q.receive(now)
            self.assertEqual(body, "poison")
            q.nack(receipt, now)  # the consumer crashed on it
            now += 1
        _, body, receipt = q.receive(now)
        self.assertEqual(body, "fine", "after 3 failed deliveries, skip the poison message")
        self.assertEqual(q.dead_letters, ["poison"])
        q.ack(receipt)
        self.assertIsNone(q.receive(now + 100), "the poison message doesn't come back")


class TopicTest(unittest.TestCase):
    def test_keyed_messages(self):
        """keeps each key's messages in order in one partition"""
        t = Topic(4)
        seen = defaultdict(list)
        for i in range(30):
            key = f"user:{i % 5}"
            p, offset = t.publish(key, i)
            self.assertEqual(p, stable_hash(key) % 4)
            seen[key].append((p, offset))
        for key, places in seen.items():
            self.assertEqual(len({p for p, _ in places}), 1, f"{key} must stay in one partition")
            offsets = [o for _, o in places]
            self.assertEqual(offsets, sorted(offsets))

    def test_offsets_and_reads(self):
        """numbers records per partition and reads without removing"""
        t = Topic(3)
        self.assertEqual([t.publish(None, v) for v in "abcdefg"], [(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (0, 2)])
        self.assertEqual(t.read(0, 0), [(0, None, "a"), (1, None, "d"), (2, None, "g")])
        self.assertEqual(t.read(0, 1, max_messages=1), [(1, None, "d")])
        self.assertEqual(t.read(0, 0), t.read(0, 0), "reading doesn't consume")
        self.assertEqual(t.read(1, 5), [])
        self.assertEqual([t.end_offset(p) for p in range(3)], [3, 2, 2])


class ConsumerGroupTest(unittest.TestCase):
    def setUp(self):
        self.topic = Topic(4)
        for i in range(8):
            self.topic.publish(None, f"event-{i}")  # two per partition

    def test_one_consumer(self):
        """gives a lone consumer every partition"""
        g = ConsumerGroup(self.topic)
        g.join("c1")
        self.assertEqual(g.assignment("c1"), [0, 1, 2, 3])
        records = g.poll("c1", max_messages=100)
        self.assertEqual(sorted(r[3] for r in records), [f"event-{i}" for i in range(8)])
        self.assertEqual(g.poll("c1"), [], "poll continues where the last one stopped")

    def test_range_assignment(self):
        """splits partitions into contiguous ranges by consumer name"""
        t = Topic(7)
        g = ConsumerGroup(t)
        for c in ("c3", "c1", "c2"):
            g.join(c)
        self.assertEqual([g.assignment(c) for c in ("c1", "c2", "c3")], [[0, 1, 2], [3, 4], [5, 6]])
        g = ConsumerGroup(Topic(2))
        for c in ("a", "b", "c"):
            g.join(c)
        self.assertEqual([g.assignment(c) for c in "abc"], [[0], [1], []], "extra consumers sit idle")

    def test_poll_limit(self):
        """returns at most max_messages records"""
        g = ConsumerGroup(self.topic)
        g.join("c1")
        first = g.poll("c1", max_messages=3)
        self.assertEqual(len(first), 3)
        rest = g.poll("c1", max_messages=100)
        self.assertEqual(len(first) + len(rest), 8)
        self.assertEqual({(r[0], r[1]) for r in first} & {(r[0], r[1]) for r in rest}, set())

    def test_rebalance_redelivers_uncommitted(self):
        """redelivers uncommitted records after a rebalance"""
        g = ConsumerGroup(self.topic)
        g.join("c1")
        g.poll("c1", max_messages=100)
        g.commit("c1")
        for i in range(8, 12):
            self.topic.publish(None, f"event-{i}")
        self.assertEqual(len(g.poll("c1", max_messages=100)), 4)  # processed, but not committed
        g.join("c2")  # rebalance: c2 takes partitions 2 and 3
        again = g.poll("c1", max_messages=100) + g.poll("c2", max_messages=100)
        self.assertEqual(sorted(r[3] for r in again), sorted(f"event-{i}" for i in range(8, 12)), "at-least-once")
        g.commit("c1")
        g.commit("c2")
        self.assertEqual(g.lag(), 0)

    def test_leave(self):
        """hands a departed consumer's partitions to the others"""
        g = ConsumerGroup(self.topic)
        g.join("c1")
        g.join("c2")
        self.assertEqual(len(g.poll("c2", max_messages=100)), 4)
        g.commit("c2")
        g.leave("c2")
        self.assertEqual(g.assignment("c1"), [0, 1, 2, 3])
        self.assertEqual(len(g.poll("c1", max_messages=100)), 4, "c2's committed records aren't redelivered")

    def test_lag(self):
        """measures lag as published minus committed"""
        g = ConsumerGroup(self.topic)
        g.join("c1")
        self.assertEqual(g.lag(), 8)
        g.poll("c1", max_messages=5)
        self.assertEqual(g.lag(), 8, "polling alone doesn't commit")
        g.commit("c1")
        self.assertEqual(g.lag(), 3)

    def test_groups_are_independent(self):
        """lets every group read the whole topic (publish-subscribe)"""
        search, emails = ConsumerGroup(self.topic), ConsumerGroup(self.topic)
        search.join("indexer")
        emails.join("mailer-1")
        emails.join("mailer-2")
        got_search = search.poll("indexer", max_messages=100)
        search.commit("indexer")
        got_emails = emails.poll("mailer-1", max_messages=100) + emails.poll("mailer-2", max_messages=100)
        self.assertEqual(len(got_search), 8)
        self.assertEqual(sorted(r[3] for r in got_emails), sorted(r[3] for r in got_search))
        self.assertEqual((search.lag(), emails.lag()), (0, 8))


if __name__ == "__main__":
    unittest.main()
