# Reliability, Scalability, and the Language of Load

*Part I · Foundations. Based on* Designing Data-Intensive Applications*, Chapter 1.*

Most applications today are **data-intensive** rather than compute-intensive. The hard part isn't raw CPU. It's the amount of data, how complex it is, and how fast it changes. You build them from standard pieces: databases, caches, search indexes, stream processors, and batch jobs. System design is the craft of choosing and combining those pieces so the whole stays **reliable**, **scalable**, and **maintainable**.

This course gives you a vocabulary first, then puts it to work: you'll estimate load on paper, wire architectures in the simulator, and build a storage engine and a consensus algorithm in code.

## Reliability: working correctly when things go wrong

A system is reliable if it keeps doing what users expect, at the expected performance, despite **faults**.

- A **fault** is one component deviating from its spec: a disk dies, a process crashes, a network link drops packets.
- A **failure** is the system as a whole no longer providing its service.

You can't prevent every fault, so you design **fault-tolerant** systems that keep faults from turning into failures. Common sources of faults:

| Kind | Examples | Typical defense |
|---|---|---|
| Hardware | Disk crashes, RAM errors, power loss, a whole machine dying | Redundancy: RAID, spare machines, multiple data centers |
| Software | A bug triggered by unusual input, a runaway process, cascading failures | Careful assumptions, testing, process isolation, monitoring |
| Human | A bad config push, a mistaken command | Good defaults, sandboxes, quick rollback, gradual rollouts |

Netflix's Chaos Monkey famously *causes* faults on purpose, so the team learns whether their fault tolerance actually works. The simulator's **Chaos** toolkit does the same for your designs.

## Scalability: coping with more load

"Does it scale?" is meaningless on its own. The useful question is: *if load grows in a particular way, what happens to performance, and what can we add to cope?*

### Describing load: load parameters

**Load parameters** are the numbers that describe the load on your system. Which ones matter depends on the architecture:

- Requests per second to a web server
- The ratio of reads to writes in a database
- Simultaneously active users in a chat room
- Cache hit rate
- **Fan-out**: how many downstream requests one incoming request causes

Twitter is the classic example. Posting a tweet is rare (about 4,600 per second on average in 2012, 12,000 at peak). Reading home timelines is common (300,000 per second). The hard part is **fan-out**. Each tweet has to reach every follower's timeline. Twitter switched from assembling timelines when you read them to pushing each new tweet into followers' cached timelines when it's written. Reads got cheap, and writes got expensive. For the few accounts with tens of millions of followers, that write fan-out was too costly, so those tweets are merged in at read time instead. The **distribution of followers per user** turned out to be a key load parameter. You'll design this system in the capstone.

### Describing performance

Two ways to look at it:

- **Throughput**: how many requests (or records, or bytes) the system processes per second. This matters most for batch work.
- **Response time**: how long a client waits from sending a request to getting a response. This matters most for online services.

People often say **latency** for response time. Strictly, latency is the time a request spends *waiting* to be handled. Response time is everything the client sees: service time plus network delays plus queueing delays.

Response time isn't one number. Run the same request a thousand times and you get a **distribution**. Some requests are slow because of a garbage collection pause, a lost packet that had to be retransmitted, or a cold cache.

### Percentiles

The **mean** is a poor summary, because it doesn't tell you how many users actually experienced a delay. Use **percentiles** instead. Sort all response times from fastest to slowest:

- **p50** (the median): half of requests are faster than this. It's the typical experience.
- **p95, p99, p999**: 95%, 99%, or 99.9% of requests are faster. These measure **tail latency**.

If p99 is 1.5 seconds, 1 in 100 requests takes at least 1.5 seconds. That sounds rare, but tails matter for two reasons:

1. **Your best customers hit them most.** The users with the most data or the most activity tend to make the slowest requests. Amazon sets internal targets at p999 for exactly this reason.
2. **Tail latency amplification.** If one page load makes 10 backend calls in parallel, it's as slow as the *slowest* call. With 10 calls, about 10% of page loads hit at least one p99-slow call.

Targets on percentiles are written into **SLOs** (service level objectives, your internal goals) and **SLAs** (contracts that promise them to customers), for example "p99 below 200 ms, 99.9% of the time."

### Queueing: why latency explodes near capacity

A server can only work on so many requests at once. Once requests arrive faster than it can finish them, they **queue**. Every new arrival waits behind everyone already in line. Waiting time doesn't grow gently: past full utilization the queue grows without bound, and response times rise steeply with it. A few slow requests can also hold up the ones behind them. This is **head-of-line blocking**.

This is the most important intuition for the simulator: **watch utilization**. Around 70% busy, queues start forming in bursts. Near 100%, they run away.

### Approaches to scaling

- **Scaling up (vertical)**: a more powerful machine. It's simple, but big machines cost disproportionately more and have a ceiling.
- **Scaling out (horizontal)**: more machines sharing the load (a **shared-nothing** architecture). There's no ceiling, but stateful parts like databases become much harder.
- **Elastic** systems add capacity automatically as load rises.

Stateless services (like API servers) are easy to scale out behind a load balancer. **Data** is the hard part. That's why most of this course is about replicating, partitioning, and moving data.

## Maintainability

Most of a system's cost comes after launch: fixing bugs, keeping it running, adapting it to new needs. Three principles help:

- **Operability**: easy for operators to keep running, with good monitoring, predictable behavior, and sane defaults.
- **Simplicity**: managing complexity with good **abstractions** that hide implementation details behind clean interfaces.
- **Evolvability**: easy to change. You'll see this again with schema evolution and rolling deployments.

## Key terms

| Term | Meaning |
|---|---|
| Fault vs. failure | One component misbehaving vs. the whole system failing users |
| Load parameter | A number describing load: requests/s, read:write ratio, fan-out |
| Throughput | Work completed per second |
| Response time | What the client waits; includes queueing and network delays |
| p50 / p99 | The response time 50% / 99% of requests beat |
| Tail latency | The slow end of the distribution (p99 and beyond) |
| Utilization | The fraction of a resource's capacity in use |
| Scale up / scale out | Bigger machine / more machines |

Next, you'll practice turning load parameters into concrete numbers with back-of-the-envelope estimates.
