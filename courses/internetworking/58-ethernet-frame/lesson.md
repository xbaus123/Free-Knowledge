# The Ethernet Frame

*Chapter 3 · The Data Link Layer.*

Ethernet is by far the most common wired link protocol, so its frame is the one to know by heart. The version used for nearly all traffic today is **Ethernet II** (also called DIX Ethernet).

## The fields

```
 ┌──────────┬──────────┬───────────┬───────────────────────┬────────┐
 │ Dest MAC │ Src MAC  │ EtherType │ Data (the datagram)   │  FCS   │
 │ 6 bytes  │ 6 bytes  │ 2 bytes   │ 46 to 1500 bytes      │ 4 bytes│
 └──────────┴──────────┴───────────┴───────────────────────┴────────┘
 ◀────── data link header ───────▶ ◀────── data and CRC (FCS) ─────▶
```

| Field | Size | What it holds |
|---|---|---|
| **Destination MAC** | 6 bytes | The hardware address of the neighbor the frame is for. It comes **first** so a NIC can decide quickly whether the frame is for it |
| **Source MAC** | 6 bytes | The hardware address of the sender |
| **EtherType** | 2 bytes | What's inside: `0x0800` is IPv4, `0x86DD` is IPv6, `0x0806` is ARP. The receiver uses it to pick which layer 3 protocol gets the data |
| **Data** | 46 to 1500 bytes | The payload: usually an IP datagram |
| **FCS** | 4 bytes | The **Frame Check Sequence**: a CRC-32 checksum over the whole frame, the final part of the frame. More on it soon |

The 14-byte header (destination, source, type) is in front of the data. The FCS is a **trailer**, behind it.

On the wire, every frame is also preceded by 8 bytes of **preamble** (alternating 1s and 0s for clock sync, ending in a *start frame delimiter*). That's how the receiver recognizes where a frame begins. The preamble isn't counted as part of the frame.

## Size limits

- **Maximum**: the data field is at most **1500 bytes**. That figure is Ethernet's **MTU (maximum transmission unit)**, the default largest packet the network layer may hand down. Add the 14-byte header and 4-byte FCS and the largest standard frame is **1518 bytes**.
- **Minimum**: a frame must be at least **64 bytes** (6 + 6 + 2 + 46 + 4). If the datagram is shorter than 46 bytes, the NIC adds **padding**. A frame shorter than 64 bytes is a **runt** and is thrown away. (You'll see why the minimum exists when we get to collisions.)
- You'll sometimes see **84 bytes** quoted as a minimum. That's what the smallest frame really occupies on the wire: 64 bytes of frame + 8 of preamble + 12 bytes' worth of mandatory idle time (the *inter-frame gap*) before the next frame.
- **Jumbo frames**: Gigabit Ethernet and faster can be configured for larger frames, commonly up to 9000 bytes of data (sometimes called giant frames). Fewer, bigger frames mean less header overhead for bulk transfers like storage traffic. Every device on the path has to agree on the larger MTU, though.

## A worked example

A host sends a 20-byte datagram. The data field must be 46 bytes, so the NIC adds 26 bytes of padding. The frame is 14 + 46 + 4 = 64 bytes.

A host sends a 1500-byte datagram: no padding, and the frame is 14 + 1500 + 4 = 1518 bytes. A 1501-byte datagram doesn't fit at all: the network layer has to break it up first.

Next, a check on the Ethernet frame.
