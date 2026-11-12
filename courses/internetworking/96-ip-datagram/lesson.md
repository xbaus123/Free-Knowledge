# The IP Datagram

*Chapter 4 · The Network Layer.*

Every IPv4 packet starts with a **header** of at least **20 bytes**, laid out in rows of 32 bits:

```
 0       4       8              16      19                     31
┌───────┬───────┬───────────────┬──────────────────────────────┐
│Version│  IHL  │ Type of Svc   │         Total length         │
├───────┴───────┴───────────────┼──────┬───────────────────────┤
│        Identification         │Flags │    Fragment offset    │
├───────────────┬───────────────┼──────┴───────────────────────┤
│      TTL      │   Protocol    │       Header checksum        │
├───────────────┴───────────────┴──────────────────────────────┤
│                    Source IP address (32 bits)               │
├──────────────────────────────────────────────────────────────┤
│                 Destination IP address (32 bits)             │
├──────────────────────────────────────────────────────────────┤
│                      Options (if any)                        │
├──────────────────────────────────────────────────────────────┤
│                            Data                              │
└──────────────────────────────────────────────────────────────┘
```

## The fields that matter most

| Field | Size | What it does |
|---|---|---|
| **Version** | 4 bits | `4` for IPv4 |
| **IHL** (header length) | 4 bits | The header's length in **32-bit words**. Without options it's 5: 5 × 4 = 20 bytes |
| **Type of service** | 8 bits | A priority class for the packet (used by the scheduling you'll meet later this chapter) |
| **Total length** | 16 bits | The size of the whole datagram, **header + data**, in bytes. At most 65,535 |
| **Identification, flags, fragment offset** | 16, 3, 13 bits | Splitting a big datagram into **fragments** that fit the next link, and putting them back together |
| **TTL** (time to live) | 8 bits | A hop limit. Every router subtracts 1; at **0** the packet is dropped |
| **Protocol** | 8 bits | What's inside: **1 = ICMP, 6 = TCP, 17 = UDP** |
| **Header checksum** | 16 bits | Catches corruption of the **header** (not the data) |
| **Source / destination address** | 32 bits each | The sending host and the intended receiving host |

## Three fields worth a closer look

**TTL stops loops.** If routers ever disagree about a route, a packet could circle between them forever. Because each router decrements the TTL, a looping packet dies after at most 255 hops. You'll see TTL again in `ping` output, and `traceroute` is built on it.

**The flags** are three bits: one unused, **DF** (*Don't Fragment*), and **MF** (*More Fragments*). Every fragment except the last has MF set. The **fragment offset** says where this fragment's data belongs in the original, counted in units of 8 bytes.

**The checksum is recomputed at every hop.** Each router changes the TTL, so the header changes, so its checksum has to be recalculated before the packet goes out again. It covers only the header: protecting the data is left to the layers above (and the frame's CRC below).

Next, a check on the IP header.
