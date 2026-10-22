"""Two kinds of message broker: a task queue with acknowledgments, and a
partitioned log with consumer groups.

Time is passed in explicitly as now (seconds), so nothing here sleeps.
"""

import hashlib


def stable_hash(text):
    """A 64-bit hash that's the same in every process (unlike hash())."""
    return int.from_bytes(hashlib.md5(text.encode("utf-8")).digest()[:8], "big")


# --- 1. A task queue -------------------------------------------------------


class TaskQueue:
    """Like SQS: each message goes to one consumer, which must acknowledge
    it before its visibility timeout runs out, or it's delivered again."""

    def __init__(self, visibility_timeout=30, max_receives=3):
        self.visibility_timeout = visibility_timeout
        self.max_receives = max_receives
        self.dead_letters = []  # bodies of messages that failed too often

    def send(self, body):
        """Add a message. Return its id."""
        raise NotImplementedError

    def receive(self, now):
        """Deliver the oldest visible message as (id, body, receipt), or
        return None. It stays hidden until now + visibility_timeout."""
        raise NotImplementedError

    def ack(self, receipt):
        """Delete the message. Return False if receipt isn't from its latest delivery."""
        raise NotImplementedError

    def nack(self, receipt, now):
        """Give the message back: visible again right away. Return False for a stale receipt."""
        raise NotImplementedError


# --- 2. A partitioned log ------------------------------------------------------


class Topic:
    """Like a Kafka topic: append-only partitions. Reading never removes anything."""

    def __init__(self, partitions):
        self.partitions = [[] for _ in range(partitions)]  # each a list of (key, value)

    def publish(self, key, value):
        """Append to the key's partition (or round robin when key is None).
        Return (partition, offset)."""
        raise NotImplementedError

    def read(self, partition, offset, max_messages=100):
        """Up to max_messages records from offset on: [(offset, key, value), ...]."""
        raise NotImplementedError

    def end_offset(self, partition):
        """The offset the next message in this partition will get."""
        raise NotImplementedError


# --- 3. Consumer groups ------------------------------------------------------


class ConsumerGroup:
    """Shares a topic's partitions among its consumers. Each partition has
    one owner in the group; each group has its own offsets."""

    def __init__(self, topic):
        self.topic = topic

    def join(self, consumer):
        raise NotImplementedError

    def leave(self, consumer):
        raise NotImplementedError

    def assignment(self, consumer):
        """The partitions this consumer owns, in order."""
        raise NotImplementedError

    def poll(self, consumer, max_messages=10):
        """The next records from the consumer's partitions:
        [(partition, offset, key, value), ...]."""
        raise NotImplementedError

    def commit(self, consumer):
        """Record the consumer's progress in each partition it owns."""
        raise NotImplementedError

    def lag(self):
        """Records published but not yet committed, over all partitions."""
        raise NotImplementedError
