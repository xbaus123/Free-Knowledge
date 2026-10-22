"""Two kinds of message broker: a task queue with acknowledgments, and a
partitioned log with consumer groups."""

import hashlib
import itertools


def stable_hash(text):
    """A 64-bit hash that's the same in every process (unlike hash())."""
    return int.from_bytes(hashlib.md5(text.encode("utf-8")).digest()[:8], "big")


# --- 1. A task queue -------------------------------------------------------


class TaskQueue:
    def __init__(self, visibility_timeout=30, max_receives=3):
        self.visibility_timeout = visibility_timeout
        self.max_receives = max_receives
        self.messages = {}  # id -> {"body", "visible_at", "receives", "receipt"}; insertion order is send order
        self.dead_letters = []
        self._ids = itertools.count(1)

    def send(self, body):
        id = f"m{next(self._ids)}"
        self.messages[id] = {"body": body, "visible_at": 0, "receives": 0, "receipt": None}
        return id

    def receive(self, now):
        for id, m in list(self.messages.items()):
            if m["visible_at"] > now:
                continue
            if m["receives"] >= self.max_receives:  # a poison message: park it
                self.dead_letters.append(m["body"])
                del self.messages[id]
                continue
            m["receives"] += 1
            m["visible_at"] = now + self.visibility_timeout
            m["receipt"] = f"{id}/{m['receives']}"
            return id, m["body"], m["receipt"]
        return None

    def _by_receipt(self, receipt):
        id = receipt.split("/")[0]
        m = self.messages.get(id)
        return (id, m) if m and m["receipt"] == receipt else (id, None)

    def ack(self, receipt):
        id, m = self._by_receipt(receipt)
        if m is None:
            return False
        del self.messages[id]
        return True

    def nack(self, receipt, now):
        _, m = self._by_receipt(receipt)
        if m is None:
            return False
        m["visible_at"] = now
        return True


# --- 2. A partitioned log ------------------------------------------------------


class Topic:
    def __init__(self, partitions):
        self.partitions = [[] for _ in range(partitions)]
        self._next = 0

    def publish(self, key, value):
        if key is None:
            p = self._next % len(self.partitions)
            self._next += 1
        else:
            p = stable_hash(key) % len(self.partitions)
        self.partitions[p].append((key, value))
        return p, len(self.partitions[p]) - 1

    def read(self, partition, offset, max_messages=100):
        log = self.partitions[partition]
        return [(o, *log[o]) for o in range(offset, min(len(log), offset + max_messages))]

    def end_offset(self, partition):
        return len(self.partitions[partition])


# --- 3. Consumer groups ------------------------------------------------------


class ConsumerGroup:
    def __init__(self, topic):
        self.topic = topic
        self.members = []
        self.assignments = {}
        n = len(topic.partitions)
        self.committed = {p: 0 for p in range(n)}
        self.position = dict(self.committed)

    def join(self, consumer):
        self.members.append(consumer)
        self.rebalance()

    def leave(self, consumer):
        self.members.remove(consumer)
        self.rebalance()

    def rebalance(self):
        members = sorted(self.members)
        n = len(self.topic.partitions)
        self.assignments = {}
        start = 0
        for i, consumer in enumerate(members):
            count = n // len(members) + (1 if i < n % len(members) else 0)
            self.assignments[consumer] = list(range(start, start + count))
            start += count
        # Everyone restarts from the last committed offsets.
        self.position = dict(self.committed)

    def assignment(self, consumer):
        return list(self.assignments.get(consumer, []))

    def poll(self, consumer, max_messages=10):
        out = []
        for p in self.assignment(consumer):
            if len(out) >= max_messages:
                break
            for offset, key, value in self.topic.read(p, self.position[p], max_messages - len(out)):
                out.append((p, offset, key, value))
                self.position[p] = offset + 1
        return out

    def commit(self, consumer):
        for p in self.assignment(consumer):
            self.committed[p] = self.position[p]

    def lag(self):
        return sum(self.topic.end_offset(p) - self.committed[p] for p in self.committed)
