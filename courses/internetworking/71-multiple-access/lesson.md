# Sharing a Channel: Multiple Access

*Chapter 3 · The Data Link Layer.*

Some links have exactly two ends. Others are shared by many devices at once. When the medium is shared, the link layer needs rules for **who gets to talk when**.

## Two kinds of link

**Point-to-point**: one sender, one receiver, one wire between them.
- The link between an Ethernet **switch and a host** (each switch port is its own link).
- **PPP** (the Point-to-Point Protocol), used for dial-up access and many WAN links.

**Broadcast (shared wire or medium)**: many nodes on one channel, and everything sent is heard by everyone.
- **Old-school Ethernet**: one coax cable or a hub, shared by every machine (the bus topology from Chapter 2).
- **Upstream cable internet (HFC)**: all the homes in a neighborhood share the same cable back to the provider.
- **802.11 WiFi**, **4G/5G cellular**, and **satellite**: all share the same radio frequencies.

The human version is a cocktail party: everyone shares the same air, and if two people talk at once, nobody understands either of them.

## Collisions

On a broadcast channel, if two or more nodes transmit at the same time, their signals mix together and the receiver gets garbage. That's a **collision**, and both frames are lost.

A **multiple access protocol** is a distributed algorithm that decides how nodes share the channel. The catch: the nodes have to coordinate using **the same channel** they're trying to share. There's no separate channel for "may I speak?"

## Three families

| Family | Idea | Collisions? | Examples |
|---|---|---|---|
| **Channel partitioning** | Divide the channel into fixed pieces (time slots, frequencies, or codes) and give each node its own exclusive piece | None: each node has exclusive use of its piece | TDMA, FDMA, CDMA |
| **Random access** | Don't divide anything. Send at full speed whenever you have data, and **recover** when frames collide | Yes, and the protocol detects and recovers from them | ALOHA, CSMA, CSMA/CD, CSMA/CA |
| **Taking turns** | Nodes take turns, so only one sends at a time. Someone with more to send waits for their turn | No | Polling, token passing (Token Ring) |

Each has a weakness:

- **Partitioning** wastes capacity when a node has nothing to send: its slot or band sits idle.
- **Random access** wastes time on collisions when traffic is heavy.
- **Taking turns** adds overhead and delay, and a node with a large datagram can hog the channel for its whole turn. In token passing, losing the token stops everyone.

The next lessons take each family in turn.

Next, a check on links and multiple access.
