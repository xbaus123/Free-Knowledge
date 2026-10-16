"""A simulated network for running several Raft nodes. (Read-only.)

The tests (and you, in the Scratchpad) run your RaftNode class here:
several instances, each with its own clock-driven tick, talking over a
network with random delays. Time is simulated, so runs are fast and the
same seed always gives the same run.

    from cluster import Cluster
    from raft import RaftNode

    c = Cluster(RaftNode, n=3, seed=1)
    c.run(1000)              # milliseconds of simulated time
    print(c.leaders())       # e.g. ["n2"]
    c.kill("n2")             # it stops; messages to and from it are lost
    c.run(1000)
    c.revive("n2")           # it resumes where it left off, unaware time passed
    c.partition(["n1"], ["n2", "n3"])   # only nodes in the same group can talk
    c.heal()
"""

import heapq
import random

from messages import Vote

TICK_MS = 5


class Env:
    """What a node can see and do: the time, randomness, and send()."""

    def __init__(self, cluster, node_id, seed):
        self._cluster = cluster
        self._id = node_id
        self.random = random.Random(seed)

    @property
    def now(self):
        """Simulated milliseconds since the cluster started."""
        return self._cluster.now

    def send(self, to, msg):
        self._cluster._send(self._id, to, msg)


class Cluster:
    def __init__(self, node_class, n=3, seed=0, latency=(2, 10), drop=0.0):
        self.now = 0
        self.ids = [f"n{i + 1}" for i in range(n)]
        self._rng = random.Random(seed)
        self._latency, self._drop = latency, drop
        self._queue, self._seq = [], 0
        self.down = set()
        self._groups = None
        self.nodes = {}
        for i, nid in enumerate(self.ids):
            peers = [p for p in self.ids if p != nid]
            self.nodes[nid] = node_class(nid, peers, Env(self, nid, seed * 1000 + i))
        # Safety records: the leader of each term, any term with two
        # leaders, and every vote granted.
        self.leader_of_term = {}
        self.violations = []
        self.votes_granted = []

    # --- faults ---

    def kill(self, nid):
        self.down.add(nid)

    def revive(self, nid):
        self.down.discard(nid)

    def partition(self, *groups):
        self._groups = [set(g) for g in groups]

    def heal(self):
        self._groups = None

    def _connected(self, a, b):
        if a in self.down or b in self.down:
            return False
        return self._groups is None or any(a in g and b in g for g in self._groups)

    # --- running ---

    def _send(self, frm, to, msg):
        if to not in self.nodes or to == frm:
            raise ValueError(f"{frm} sent a message to unknown node {to!r}")
        if isinstance(msg, Vote) and msg.granted:
            self.votes_granted.append((msg.voter, msg.term, to))
        if not self._connected(frm, to) or self._rng.random() < self._drop:
            return
        self._seq += 1
        heapq.heappush(self._queue, (self.now + self._rng.uniform(*self._latency), self._seq, frm, to, msg))

    def step(self):
        """Advances time by one tick: delivers due messages, then ticks every live node."""
        self.now += TICK_MS
        while self._queue and self._queue[0][0] <= self.now:
            _, _, frm, to, msg = heapq.heappop(self._queue)
            if self._connected(frm, to):
                self.nodes[to].on_message(msg)
        for nid in self.ids:
            if nid not in self.down:
                self.nodes[nid].tick()
        for nid in self.ids:
            node = self.nodes[nid]
            if nid not in self.down and node.role == "leader":
                first = self.leader_of_term.setdefault(node.term, nid)
                if first != nid:
                    self.violations.append((self.now, node.term, first, nid))

    def run(self, ms):
        for _ in range(int(ms // TICK_MS)):
            self.step()

    def run_until(self, condition, limit_ms):
        """Steps until condition() is true; returns the ms it took, or None."""
        start = self.now
        while self.now - start < limit_ms:
            if condition():
                return self.now - start
            self.step()
        return self.now - start if condition() else None

    # --- inspecting ---

    def leaders(self, among=None):
        """Live nodes that believe they're the leader."""
        ids = among or self.ids
        return [nid for nid in ids if nid not in self.down and self.nodes[nid].role == "leader"]

    def leader(self):
        """The leader with the highest term, if any."""
        live = self.leaders()
        return max(live, key=lambda nid: self.nodes[nid].term) if live else None
