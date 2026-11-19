"""Raft leader election and heartbeats."""

from messages import Heartbeat, HeartbeatReply, RequestVote, Vote

ELECTION_TIMEOUT_MS = (150, 300)
HEARTBEAT_MS = 50


class RaftNode:
    def __init__(self, node_id, peers, env):
        self.id = node_id
        self.peers = peers  # the other nodes' ids
        self.env = env  # env.now, env.random, env.send(to, msg)
        self.term = 0
        self.voted_for = None
        self.role = "follower"  # "follower", "candidate", or "leader"
        self.leader_id = None
        self.votes = set()
        self.next_heartbeat = 0
        self.reset_election_timer()

    def reset_election_timer(self):
        """Picks a new random deadline for hearing from a leader."""
        self.election_deadline = self.env.now + self.env.random.uniform(*ELECTION_TIMEOUT_MS)

    def majority(self):
        return (len(self.peers) + 1) // 2 + 1

    def broadcast(self, msg):
        for peer in self.peers:
            self.env.send(peer, msg)

    # --- time passing ---

    def tick(self):
        if self.role == "leader":
            if self.env.now >= self.next_heartbeat:
                self.broadcast(Heartbeat(self.term, self.id))
                self.next_heartbeat = self.env.now + HEARTBEAT_MS
        elif self.env.now >= self.election_deadline:
            self.start_election()

    def start_election(self):
        self.term += 1
        self.role = "candidate"
        self.voted_for = self.id
        self.votes = {self.id}
        self.leader_id = None
        self.reset_election_timer()  # if this election splits, try again
        self.broadcast(RequestVote(self.term, self.id))

    def become_follower(self, term):
        """Steps down into a newer term. The timer restarts so the current
        leader has time to reach us before we call an election."""
        self.term = term
        self.role = "follower"
        self.voted_for = None
        self.votes = set()
        self.reset_election_timer()

    def become_leader(self):
        self.role = "leader"
        self.leader_id = self.id
        self.next_heartbeat = self.env.now  # announce right away
        self.tick()

    # --- messages ---

    def on_message(self, msg):
        # Any message from a newer term means we're behind: step down.
        if msg.term > self.term:
            self.become_follower(msg.term)

        if isinstance(msg, RequestVote):
            grant = msg.term == self.term and self.voted_for in (None, msg.candidate)
            if grant:
                self.voted_for = msg.candidate
                self.reset_election_timer()
            self.env.send(msg.candidate, Vote(self.term, self.id, grant))

        elif isinstance(msg, Vote):
            if self.role == "candidate" and msg.term == self.term and msg.granted:
                self.votes.add(msg.voter)
                if len(self.votes) >= self.majority():
                    self.become_leader()

        elif isinstance(msg, Heartbeat):
            if msg.term == self.term:
                self.role = "follower"  # a candidate who lost to this leader
                self.leader_id = msg.leader
                self.reset_election_timer()
            self.env.send(msg.leader, HeartbeatReply(self.term, self.id))

        elif isinstance(msg, HeartbeatReply):
            pass  # a newer term in a reply already made us step down above
