"""Messages Raft nodes send each other. (Read-only.)

Every message carries the sender's current term. Leader election uses
RequestVote and Vote; leaders assert themselves with Heartbeat (an
AppendEntries call with no log entries) every HEARTBEAT_MS.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class RequestVote:
    term: int
    candidate: str


@dataclass(frozen=True)
class Vote:
    term: int
    voter: str
    granted: bool


@dataclass(frozen=True)
class Heartbeat:
    term: int
    leader: str


@dataclass(frozen=True)
class HeartbeatReply:
    term: int
    follower: str
