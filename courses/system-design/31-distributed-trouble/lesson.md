# The Trouble with Distributed Systems

*Based on* Designing Data-Intensive Applications*, Chapter 8.*

On one computer, things usually either work or crash. In a distributed system, **partial failures** are normal: some parts break in unpredictable ways while others carry on, and you often can't even tell which. Three sources of trouble dominate.

## Unreliable networks

Datacenter networks are **asynchronous packet networks**: a message can be lost, delayed, duplicated, or reordered, with no upper bound on delay. When you send a request and get no response, you **can't tell** whether:

- the request was lost,
- the remote node is down,
- the remote node is just slow (overloaded, or paused),
- or the request succeeded and the *response* was lost.

The only tool is a **timeout**, and there's no correct value. Too short, and you declare live nodes dead, triggering failovers that add load and can cascade. Too long, and you wait ages for nodes that really are dead. Queueing in switches, in the OS, and in the application makes network delay vary wildly.

## Unreliable clocks

Each machine has its own quartz clock, which **drifts** (Google assumes 200 ppm, about 6 ms of error every 30 seconds). Two kinds of clock matter:

- **Time-of-day clocks** (`time.time()`, `System.currentTimeMillis()`) return wall-clock time, synchronized with **NTP**. They can **jump backward or forward** when NTP corrects them, so they're unsuitable for measuring durations.
- **Monotonic clocks** (`time.monotonic()`, `System.nanoTime()`) only move forward. They're good for measuring elapsed time on one machine, but meaningless to compare across machines.

**Last write wins** conflict resolution (Cassandra, Riak) orders writes by the timestamps of different machines' time-of-day clocks. A node whose clock runs a few milliseconds fast can make its writes win over writes that actually happened later, **silently discarding data**. Google's Spanner instead reports a **confidence interval** for the time (TrueTime) and waits out the uncertainty before committing.

## Process pauses

A thread can be paused for a long time without noticing:

- **Garbage collection** "stop-the-world" pauses, sometimes lasting seconds.
- A **virtual machine** being suspended or live-migrated.
- The OS swapping to disk, or a laptop lid closing.
- `SIGSTOP`, or a slow synchronous disk read.

The danger is code that checks a condition and then acts on it, assuming no time passed in between:

```java
while (true) {
    request = getIncomingRequest();
    if (lease.expiryTimeMillis - System.currentTimeMillis() > 10000) {   // check
        process(request);                                                // act
    }
}
```

If the thread pauses for 15 seconds right after the check, its lease expires, another node takes over, and then this node wakes and processes the request anyway, **believing it still holds the lease**.

## Knowledge, truth, and lies

A node can't trust its own judgment of the situation. It might be the one cut off from the others, or the one that was paused.

- **The truth is defined by the majority.** Decisions such as declaring a node dead or electing a leader need a **quorum** of nodes to agree. A node the majority has declared dead *is* dead, even if it disagrees.
- **Split brain**: two nodes both believe they're the leader, for example because one was paused or partitioned. Both accept writes, and data gets corrupted.
- **Fencing tokens** guard against zombies. Every time the lock service grants a lease, it also hands out a token: a number that goes up with every grant. Clients include the token with every write, and storage **rejects writes with a lower token** than one it has already seen. You'll build this in lesson 33.
- **Byzantine faults**: nodes that lie, through malice or corruption. Most systems inside one organization assume nodes are honest but unreliable. Byzantine fault tolerance matters for blockchains and aerospace.

The next lesson turns this diagnosis into defenses: timeouts, retries, circuit breakers, and bulkheads.

Answer the questions on the right.
