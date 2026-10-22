"""Raft leader election and heartbeats.

Fill in the TODOs. The tests run three (and five) copies of this class in
cluster.py's simulated network, kill the leader, and check that a new one
takes over. See the lesson for the rules.
"""

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
        """Called every few milliseconds.

        TODO: a leader sends a Heartbeat to every peer every HEARTBEAT_MS.
        Anyone else starts an election once env.now passes
        self.election_deadline.
        """

    def start_election(self):
        """TODO: move to the next term, become a candidate, vote for
        yourself, reset the election timer (in case this election splits
        the vote), and ask every peer for its vote."""

    def become_follower(self, term):
        """Steps down into a newer term. The timer restarts so the current
        leader has time to reach us before we call an election."""
        self.term = term
        self.role = "follower"
        self.voted_for = None
        self.votes = set()
        self.reset_election_timer()

    def become_leader(self):
        """TODO: become leader and send heartbeats right away, so the
        other candidates stand down."""

    # --- messages ---

    def on_message(self, msg):
        """TODO: handle each message type.

        - Any message with a newer term: become a follower in that term first.
        - RequestVote: grant it (send a Vote back) only if it's for your
          current term and you haven't voted for someone else in this term.
          Reset your election timer when you grant a vote.
        - Vote: as a candidate, count granted votes for your current term;
          with a majority (counting your own), become leader.
        - Heartbeat for your current term: a leader exists, so be a
          follower, remember who leads, and reset your election timer.
          Reply with a HeartbeatReply carrying your term.
        - HeartbeatReply: nothing to do beyond the term check.
        """
