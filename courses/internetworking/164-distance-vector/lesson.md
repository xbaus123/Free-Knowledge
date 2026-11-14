# Distance Vector Routing

*Chapter 6 · Routing.*

Routing protocols come in three families:

| Family | In one line | Examples |
|---|---|---|
| **Distance vector** | Tell your **neighbors** how far you are from everything | RIP |
| **Link state** | Tell **everyone** about your own links; each router draws the whole map | OSPF, IS-IS |
| **Path vector** | Like distance vector, but advertise the **whole path**, and apply policy | BGP |

We'll take them one at a time, using the same small network throughout. The numbers are link **costs**:

```
         1          5          3
    A ──────── B ──────── D ──────── E
     \         │         /
    4 \      2 │        / 1
       \       │       /
        └───── C ─────┘
```

Links: A–B 1, A–C 4, B–C 2, B–D 5, C–D 1, D–E 3.

## What "distance" means

The **cost** of a path is the sum of its link costs. The simplest metric is **hop count**: every link costs 1. It can also be based on **delay** or **packet loss** (think of the round-trip times `ping` showed you in chapter 4's ICMP lesson). Lower is better.

## How it works

Each router keeps a **distance vector**: its best known cost to every destination, and which neighbor to send through. Then, over and over:

1. Send your vector to your **neighbors** (only them).
2. When a neighbor's vector arrives, check whether going **through that neighbor** is cheaper than what you have.
3. If anything changed, send your updated vector out. A change **triggers** more updates.

Step 2 is the **Bellman-Ford equation**. For router x and destination y:

> cost(x → y) = the minimum, over every neighbor v, of **link cost(x, v) + v's cost to y**

## Worked example: A's route to D

A's neighbors are B and C. They report:

- B: "I can reach D at cost 3" (through C: 2 + 1, cheaper than its direct link at 5)
- C: "I can reach D at cost 1"

A computes:

| Through | Link cost | + neighbor's cost to D | = Total |
|---|---|---|---|
| B | 1 | 3 | **4** |
| C | 4 | 1 | 5 |

So A's route to D is **cost 4, next hop B**, even though A is directly connected to C, which is directly connected to D. A never sees the whole map; it only trusts what its neighbors told it.

That trust raises the question the next reading answers: **how do we know a neighbor's distance is accurate, or even correct?**
