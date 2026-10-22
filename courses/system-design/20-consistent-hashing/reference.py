"""Decides which node stores each key, with a consistent hash ring."""

import bisect
import hashlib


def stable_hash(text):
    """A 64-bit hash that's the same in every process (unlike hash())."""
    return int.from_bytes(hashlib.md5(text.encode("utf-8")).digest()[:8], "big")


class Partitioner:
    def __init__(self, nodes, vnodes=160):
        """nodes: node names. vnodes: points each node gets on the ring."""
        self.vnodes = vnodes
        self.ring = []  # sorted [(point, node)]
        for node in nodes:
            self.add_node(node)

    def add_node(self, node):
        for i in range(self.vnodes):
            bisect.insort(self.ring, (stable_hash(f"{node}#{i}"), node))

    def remove_node(self, node):
        self.ring = [entry for entry in self.ring if entry[1] != node]

    def node_for(self, key):
        # The first point clockwise from the key's hash, wrapping around.
        i = bisect.bisect_right(self.ring, (stable_hash(key), "￿"))
        return self.ring[i % len(self.ring)][1]
