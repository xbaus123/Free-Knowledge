# The OSI 7-Layer Model

*Chapter 1 · Intro to Networks.*

The most widely used way to name the layers is the OSI model. Network engineers say "layer 2" or "layer 3" every day, and they mean these numbers.

## The OSI 7-layer model

The **Open Systems Interconnection (OSI)** model was published by the International Organization for Standardization (ISO) in 1984. It splits networking into seven layers. Data you send travels *down* the stack on your machine, across the physical link, then *up* the stack on the receiver:

| # | Layer | Job | Unit of data | Examples |
|---|---|---|---|---|
| 7 | **Application** | The network services programs use | Data | HTTP, SMTP, DNS, FTP |
| 6 | **Presentation** | How data is represented: encoding, compression, encryption | Data | TLS, JPEG, ASCII, UTF-8 |
| 5 | **Session** | Opening, managing, and closing conversations between programs | Data | SIP, RPC, NetBIOS |
| 4 | **Transport** | End-to-end delivery between programs: ports, reliability, ordering | **Segment** (TCP) or datagram (UDP) | TCP, UDP |
| 3 | **Network** | Addressing and routing between networks | **Packet** | IP, ICMP |
| 2 | **Data Link** | Delivery across one link, between neighbors on the same network | **Frame** | Ethernet, Wi-Fi (802.11), PPP |
| 1 | **Physical** | Signals on the medium: voltages, light pulses, radio waves | **Bits** | Cables, connectors, hubs, radios |

A common way to remember the order from layer 1 up: **P**lease **D**o **N**ot **T**hrow **S**ausage **P**izza **A**way.

### The two "missing" layers

The OSI model stops at layer 7, but network engineers like to joke about the layers above it, because that's where many real problems come from. The usual versions:

- **Layer 8: the user.** "A layer 8 problem" means the network is fine and the person at the keyboard made the mistake.
- **Layer 9: the organization.** Budgets, policies, and politics: the decisions that shape a network before anyone plugs in a cable.

They aren't part of any standard, but they're a reminder that a network design has to work for the people and the organization too.

Next, a check on the seven layers. Expect to type some answers from memory.
