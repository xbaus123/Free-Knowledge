# Random Access and Slotted ALOHA

*Chapter 3 · The Data Link Layer.*

Random access protocols take the opposite approach to partitioning: **don't divide the channel at all**.

## Random access in general

- When a node has a packet, it **transmits at the full channel data rate R**.
- There's **no a priori coordination**: nobody books a slot in advance.
- If two or more nodes transmit at once, there's a **collision**.

So a random access protocol has to specify two things: **how to detect collisions**, and **how to recover from them** (usually by retransmitting after a delay). The family includes **ALOHA** and **slotted ALOHA**, and **CSMA**, **CSMA/CD**, and **CSMA/CA**.

ALOHA was built at the University of Hawaii around 1970 to link computers across the islands by radio. It's the ancestor of Ethernet.

## Slotted ALOHA

**Assumptions:**
- All frames are the same size.
- Time is divided into equal slots, each exactly long enough to send one frame.
- Nodes only start transmitting at the **beginning** of a slot, so all nodes' clocks are **synchronized**.
- If two or more nodes transmit in the same slot, **all nodes detect the collision**.

**Operation:**
- When a node gets a fresh frame, it transmits in the **next slot**.
- **No collision**: success. The node can send another new frame in the next slot.
- **Collision**: the node retransmits the frame in **each later slot with probability p**, until it gets through.

Why the coin flip? If both colliding nodes simply retried in the next slot, they'd collide again, and again, forever. **Randomizing** means that sooner or later one retries while the other waits.

## An example

Three nodes, nine slots. C is a collision, S a success, E an empty slot:

```
 node 1 │ 1 │   │ 1 │   │   │ 1 │   │ 1 │   │
 node 2 │ 2 │   │ 2 │ 2 │   │   │   │   │   │
 node 3 │ 3 │   │   │   │   │ 3 │   │   │ 3 │
 slot   │ C │ E │ C │ S │ E │ C │ E │ S │ S │
```

Only 3 of the 9 slots carried a frame successfully. The rest were collisions or sat empty.

**Pros:** a single active node can transmit continuously at the full rate. It's **highly decentralized**: only the slot boundaries need to be in sync. It's **simple**.

**Cons:** collisions waste slots, idle slots are wasted too, a collision wastes the *whole* slot even though it could be detected sooner, and every node needs **clock synchronization**.

## Efficiency: at best 37%

**Efficiency** is the long-run fraction of slots that succeed, when many nodes all have many frames to send.

Suppose N nodes each transmit in a slot with probability p:

- A given node succeeds in a slot when it sends and the other N − 1 don't: **p(1 − p)^(N−1)**.
- *Some* node succeeds: **Np(1 − p)^(N−1)**.
- That's largest when **p = 1/N**. As N grows, the maximum heads toward **1/e ≈ 0.37**.

So **at best, the channel carries useful data 37% of the time**. A 10 Mbps slotted ALOHA channel gives about 3.7 Mbps of real throughput under heavy load. Plain (unslotted) ALOHA, where nodes start whenever they like, is worse still: 1/(2e), about 18%.

Next, a check on random access and slotted ALOHA.
