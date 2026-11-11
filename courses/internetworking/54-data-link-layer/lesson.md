# The Data Link Layer

*Chapter 3 · The Data Link Layer.*

Chapter 2 got bits onto a wire, a fiber, or the air. But a stream of bits on its own means nothing: where does one message end and the next begin? Who is it for? Did it arrive intact? Answering those questions is the job of **layer 2, the data link layer**.

## One hop at a time

The data link layer moves a packet across **one link**: from one machine to a **neighbor** it is directly connected to. Neighbors are hosts on the same LAN, on the same segment. Getting a packet across the whole Internet is layer 3's job; layer 2 only ever takes it one hop.

A packet heading across the Internet crosses many links, and each one can use a **different link protocol**:

```
 laptop ──WiFi──▶ home router ──Ethernet──▶ ISP router ──fiber──▶ ISP router ──▶ ...
         link 1                 link 2                   link 3
```

The IP packet (a **datagram**) stays the same the whole way. At every hop it's put into a fresh layer 2 **frame** for the next link, then taken out again at the other end. Think of a traveler on one trip using a taxi, then a train, then a plane: same traveler, different carrier for each leg.

## Frames

The layer 2 unit of data is the **frame**. A link protocol's **format specification** says exactly what a frame looks like: what fields it has, in what order, and the **rules for recognizing a frame's boundaries**, so the receiver knows where one frame stops and the next starts.

## What layer 2 can offer

Each link protocol picks from a menu of services. Not every protocol offers all of them:

| Service | What it means |
|---|---|
| **Framing** | Wrap the datagram in a frame with a header (and usually a trailer) |
| **Link access** | Rules for who may transmit when, if many devices share one medium |
| **Link addressing** | Hardware (MAC) addresses that say which neighbor a frame is for |
| **Flow control** | Pacing between the sender and receiver on the link, so a fast sender doesn't swamp a slow receiver |
| **Error detection** | Catching bits flipped by attenuation or noise, then dropping the frame or asking for it again |
| **Error correction** | Finding *and fixing* the flipped bits, with no retransmission |
| **Reliable delivery** | Making sure every frame gets across. Wired links rarely bother, because errors are rare. Wireless links often do |
| **Half or full duplex** | Half duplex: both ends can send, but not at the same time. Full duplex: both at once |

The chapter's four big topics fall out of that table: **error detection** (with the frame checksum), **sharing a broadcast channel**, **link layer addressing**, and the devices that build LANs and data center networks out of switches.

Next, a short check on what the data link layer is for.
