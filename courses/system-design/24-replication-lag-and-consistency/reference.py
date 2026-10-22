"""Living with replication lag: measuring it, and giving each user's session
read-your-writes, monotonic reads, and consistent prefix reads."""


class Clock:
    def __init__(self, now=0.0):
        self.now = now

    def advance(self, seconds):
        self.now += seconds


class Leader:
    """Takes every write. Each write gets the next log sequence number (LSN):
    the first write is LSN 1, and LSN 0 means the empty database."""

    def __init__(self, clock):
        self.clock = clock
        self.log = []  # [(commit time, key, value)]; entry i has LSN i + 1
        self.data = {}
        self.reads = 0

    @property
    def lsn(self):
        return len(self.log)

    def write(self, key, value):
        self.log.append((self.clock.now, key, value))
        self.data[key] = value
        return self.lsn

    def read(self, key):
        """(value, LSN of the state it was read from)."""
        self.reads += 1
        return self.data.get(key), self.lsn


class Follower:
    """Applies the leader's log asynchronously, lag seconds behind."""

    def __init__(self, name, leader, lag):
        self.name = name
        self.leader = leader
        self.lag = lag
        self.data = {}
        self.reads = 0
        self._applied = 0

    @property
    def applied_lsn(self):
        """How much of the leader's log this follower has applied."""
        log, cutoff = self.leader.log, self.leader.clock.now - self.lag
        while self._applied < len(log) and log[self._applied][0] <= cutoff:
            _, key, value = log[self._applied]
            self.data[key] = value
            self._applied += 1
        return self._applied

    def read(self, key):
        lsn = self.applied_lsn
        self.reads += 1
        return self.data.get(key), lsn


# --- 1. Measuring lag --------------------------------------------------------


def lag_report(leader, followers):
    """{follower name: (writes behind, seconds behind)}."""
    report = {}
    for f in followers:
        applied = f.applied_lsn
        behind = leader.lsn - applied
        seconds = leader.clock.now - leader.log[applied][0] if behind else 0.0
        report[f.name] = (behind, seconds)
    return report


# --- 2. Session guarantees ---------------------------------------------------


class Session:
    """One user's connection to a leader and its followers."""

    def __init__(self, leader, followers, read_your_writes=False, monotonic_reads=False):
        self.leader = leader
        self.followers = list(followers)
        self.read_your_writes = read_your_writes
        self.monotonic_reads = monotonic_reads
        self.turn = 0  # rotates which follower is tried first
        self.write_lsn = 0  # LSN of this session's latest write
        self.read_lsn = 0  # newest state this session has read

    def write(self, key, value):
        self.write_lsn = self.leader.write(key, value)

    def read(self, key):
        need = 0
        if self.read_your_writes:
            need = self.write_lsn
        if self.monotonic_reads:
            need = max(need, self.read_lsn)
        n = len(self.followers)
        order = [self.followers[(self.turn + i) % n] for i in range(n)]
        self.turn += 1
        node = next((f for f in order if f.applied_lsn >= need), self.leader)
        value, lsn = node.read(key)
        self.read_lsn = max(self.read_lsn, lsn)
        return value


# --- 3. Consistent prefix reads ----------------------------------------------


class CausalReader:
    """Merges writes arriving from several partitions' replication streams,
    and makes each visible only after every write it depends on."""

    def __init__(self):
        self.visible = []  # write ids, in the order they became visible
        self._seen = set()
        self._waiting = []  # writes whose dependencies haven't arrived

    def receive(self, write):
        """write: {"id": ..., "deps": [ids it causally depends on], ...}."""
        if write["id"] in self._seen or any(w["id"] == write["id"] for w in self._waiting):
            return
        self._waiting.append(write)
        progress = True
        while progress:
            progress = False
            for w in list(self._waiting):
                if all(d in self._seen for d in w.get("deps", ())):
                    self._waiting.remove(w)
                    self._seen.add(w["id"])
                    self.visible.append(w["id"])
                    progress = True

    def pending(self):
        """Ids of writes still waiting for their dependencies, in arrival order."""
        return [w["id"] for w in self._waiting]
