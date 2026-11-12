# The Network Layer

*Chapter 4 · The Network Layer.*

Chapter 3 moved a frame across **one link**, to a neighbor on the same LAN. That's as far as layer 2 goes. To get a packet from your laptop to a server on the other side of the world, across dozens of links run by different organizations, you need **layer 3, the network layer**, and its protocol, **IP**.

## Where we are

```
 7  Application
 6  Presentation
 5  Session
 4  Transport
 3  Network      ◀── this chapter: IP addresses, routers, ICMP
 2  Data Link    ◀── chapter 3: frames, MAC addresses, switches
 1  Physical     ◀── chapter 2: cables, fiber, radio
```

Layer 3's unit of data is the **packet**, which IP calls a **datagram**. Its addresses are **IP addresses**, and the device that works at this layer is the **router**.

## Two jobs: forwarding and routing

The network layer has two key functions. They sound alike, but they work on very different timescales:

| | Forwarding | Routing |
|---|---|---|
| What | Move a packet from a router's **input link** to the right **output link** | Work out the **whole route** packets take from source to destination |
| Where | Inside **one** router | Across the **whole** network |
| How fast | Every packet, in nanoseconds, usually in hardware | Every few seconds or minutes, in software (**routing algorithms**) |
| Trip analogy | Getting through **one interchange** on the highway | **Planning the trip** on a map before you leave |

Routing fills in each router's **forwarding table**. Forwarding reads that table for every packet that arrives. A later chapter covers routing algorithms; this one is about the addresses those tables are built from.

## Same packet, new frame at every hop

Recall from chapter 3: at each hop, the router **strips** the old frame, reads the **destination IP address** in the packet, picks the next hop, and wraps the packet in a **new frame** for the next link.

- The **IP addresses** (source and destination) stay the same from end to end.
- The **MAC addresses** change at every hop: each frame is addressed from this router to the next one.

So a MAC address answers *"which device on this wire?"* and an IP address answers *"which host on the whole Internet?"*

Next, a check on the network layer's job.
