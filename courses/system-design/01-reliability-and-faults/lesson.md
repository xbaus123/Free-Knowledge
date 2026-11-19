# Reliability: Faults and Failures

*Chapter 1 · Foundations.*

*Based on* Designing Data-Intensive Applications*, Chapter 1.*

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

Next, a short check on what you just read.
