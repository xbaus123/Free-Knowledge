# The Trouble with Distributed Systems: Fencing Tokens

Two workers share a job: every 50 ms, someone must write the next batch of results to **Storage**. Only one may write at a time, or the results interleave and corrupt each other. So the workers take turns holding a **lease** from a **Lock Service** (think ZooKeeper or etcd):

- A worker that isn't holding the lock asks for it every 50 ms.
- The holder **renews** its lease every third of the lease length, and writes while it believes it still holds the lease.
- If the holder goes silent, the lock frees up when its lease runs out, and the other worker takes over.

Click **Run Scenario**. The simulator injects two faults at 300 ms:

1. **Packets between Worker A and the Lock Service are dropped**, so A's renewals never arrive.
2. **Worker A freezes for 1.5 seconds**: a long garbage collection pause. It had just checked its lease and prepared a write when it froze.

Replay the run and watch the badges: who holds the lock, which token, and who wrote last.

## Two ways to fail

**Liveness: the job stalls.** With a 10-second lease, the lock stays with frozen Worker A long after it stopped working, and nothing gets written. The run fails if no worker writes for more than **1 second**. So shorten the lease (double-click the Lock Service).

**Safety: a zombie corrupts data.** Shorten the lease, and Worker B takes over while A is frozen. Then A wakes up and sends the write it prepared before freezing. Nothing in A's code knows time passed. It checked its lease, and then it wrote. Storage accepts it, and A's stale data overwrites B's newer data.

A shorter lease alone can't fix this. Whatever the lease length, a pause or a slow network can always outlast it. The client can't be trusted to know it's out of date; **the storage has to refuse it**.

## Your task

Wire up **fencing tokens**:

1. **Lock Service → Issue fencing tokens.** Each grant comes with a number one higher than the last: A gets 33, and B, taking over, gets 34. Workers attach their token to every write.
2. **Storage → Reject stale fencing tokens.** Storage remembers the highest token it has seen and refuses any write with a lower one. When A wakes up and sends a write with token 33 after B has written with 34, storage rejects it, and A learns it has lost the lock.
3. Pick a **lease** short enough that the job doesn't stall for more than a second.

The run passes with **zero corrupted writes** and **no stall longer than 1 second**. The results show the lease, writes accepted, stale writes rejected, corrupted writes, and the longest stall.

> **Think about it.** Fencing needs the storage to *check* tokens. What if your storage can't, like a plain file server or an old API? Some systems put the token in the data itself, using a conditional write ("only if the stored token is lower"). Others give up on locks and use idempotent, versioned writes instead. And because the lock service is itself replicated with a consensus algorithm, its tokens are trustworthy even when lock service nodes fail. That's the subject of the next lessons.
