# Why We Network

*Chapter 1 · Intro to Networks.*

Before you can reason about routers, subnets, and DNS, it helps to know why the Internet looks the way it does. Most of its odd features, like having no central hub, trusting every host, and running out of addresses, come straight out of its history.

## Why network at all?

Computers are networked to **share**:

- **Resources**: one expensive printer, disk, or supercomputer used by many people.
- **Information**: files, databases, and email between people in different places.
- **Reliability**: if one machine or site fails, the work can move to another.

In the 1960s and 70s, computers cost millions of dollars. Letting a researcher in Los Angeles use a machine in Utah, without flying there, was worth a lot of engineering.

## Networks before the Internet

The Internet wasn't the first computer network. Several came before it, and most only worked with their own kind of equipment:

| Network | Who built it | What it was |
|---|---|---|
| **AUTODIN** | US Department of Defense (1960s) | The *Automatic Digital Network*: a military message-switching system that stored whole messages at relay centers and forwarded them on |
| **DECnet** | Digital Equipment Corporation (1975) | A protocol suite for connecting DEC's own computers to each other |
| **X.25** | CCITT (now ITU) standard (1976) | Public data networks run by phone companies. The NSF-funded research network CSNET carried part of its traffic over X.25 |

Each one solved networking *inside one world*: one vendor, one agency, or one carrier. Connecting those worlds to each other is the problem the Internet was built to solve. That's what **internetworking** means: a network of networks.

## Circuit switching vs packet switching

The telephone system uses **circuit switching**. When you place a call, the network reserves a path from you to the other end for the whole call. That's great for steady voice traffic, but wasteful for computers, which send in bursts and are silent most of the time. A reserved circuit sits idle between bursts, and if any switch on the path fails, the call drops.

**Packet switching** splits data into small **packets**, each carrying its destination address. Every switch along the way looks at the address and forwards the packet on, one hop at a time. There's no reserved path:

- Links are **shared**: packets from many conversations take turns on the same wire.
- Packets of one message can take **different routes**, and the network can route around a failed link.
- The cost: packets can be delayed, lost, or arrive out of order, so the endpoints have to cope.

| | Circuit switching | Packet switching |
|---|---|---|
| Path | Reserved for the whole conversation | Chosen per packet, hop by hop |
| Idle capacity | Wasted | Used by other traffic |
| A link fails | The conversation drops | Traffic is rerouted |
| Delay | Fixed and predictable | Varies with load |
| Example | The classic phone network | The Internet |

Next, a short check on packet switching and the networks that came before the Internet.
