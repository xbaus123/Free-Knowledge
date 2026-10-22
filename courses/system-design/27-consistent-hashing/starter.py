"""Decides which node stores each key.

This version uses hash(key) mod N. It spreads keys evenly, but watch what
happens to every key's home when a node is added. Rewrite it as a
consistent hash ring with virtual nodes.
"""

import hashlib


def stable_hash(text):
    """A 64-bit hash that's the same in every process (unlike hash())."""
    return int.from_bytes(hashlib.md5(text.encode("utf-8")).digest()[:8], "big")


class Partitioner:
    def __init__(self, nodes, vnodes=100):
        """nodes: node names. vnodes: points each node gets on the ring."""
        self.vnodes = vnodes
        self.nodes = list(nodes)

    def add_node(self, node):
        self.nodes.append(node)

    def remove_node(self, node):
        self.nodes.remove(node)

    def node_for(self, key):
        return self.nodes[stable_hash(key) % len(self.nodes)]
