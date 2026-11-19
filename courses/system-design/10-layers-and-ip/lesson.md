# Network Layers and IP

*Chapter 1 · Foundations.*

Every arrow in a system diagram is a network call. When you draw "client → load balancer → server → database," each arrow hides addresses, routing, a handshake, possibly a DNS lookup, and at least one round trip. Most of the surprising behavior in distributed systems comes from those arrows: requests that are slow, lost, duplicated, or reordered. The next four readings cover what happens inside one arrow.

## The layers

Networking is built as a stack. Each layer uses the one below it and hides its details from the one above:

| Layer | Job | Examples |
|---|---|---|
| Application | What the bytes mean | HTTP, DNS, gRPC, SMTP |
| Transport | Conversations between programs | TCP, UDP, QUIC |
| Network | Getting a packet from one machine to another, across networks | IP |
| Link | Moving frames across one physical hop | Ethernet, Wi-Fi |

Your code mostly lives at the top two layers. But the guarantees you get, and the ones you don't, come from the layers underneath.

## IP: addresses and best-effort delivery

The **Internet Protocol** gives every machine an **address** and moves **packets** (chunks of up to about 1,500 bytes) toward it, one **router** hop at a time. Each router looks at the destination address and forwards the packet to a neighbor that's closer.

An **IPv4 address** is a 32-bit number, written as four bytes in decimal: `192.168.1.10` is `192·256³ + 168·256² + 1·256 + 10`. Four billion addresses ran out long ago, so **IPv6** uses 128 bits (`2001:db8::1`), and many networks share one public IPv4 address behind **NAT**.

Addresses are handed out in blocks written in **CIDR** notation: `10.0.0.0/8` means "every address whose first 8 bits match `10.0.0.0`," which is 2²⁴ ≈ 16.7 million addresses. A `/24` has 256 addresses, and a `/32` is one address. Routers and firewalls use these blocks constantly ("send `10.0.0.0/8` this way," "allow traffic from `172.16.0.0/12`"). Three blocks are **private**, reserved for internal networks and never routed on the public internet: `10.0.0.0/8`, `172.16.0.0/12`, and `192.168.0.0/16`. Your cloud servers almost certainly live in one of them.

The crucial property: **IP is best-effort**. A packet may be:

- **dropped** (a router's queue was full, a link flapped),
- **duplicated** (a retry somewhere below),
- **reordered** (two packets took different paths),
- **delayed** by an unbounded amount.

IP doesn't tell you which. Everything reliable is built on top of this unreliable base.

Next, a short check on what you just read.
