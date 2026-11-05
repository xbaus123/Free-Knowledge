# The TCP/IP Model and Where Devices Live

*Chapter 1 · Intro to Networks.*

OSI is the model people use to talk about networks. TCP/IP is the one the Internet actually runs on. This lesson maps one onto the other, and places common devices on the stack.

## The TCP/IP architecture

The OSI model is a reference for thinking and talking about networks. The Internet actually runs on the **TCP/IP** model, which is older and has four layers:

| # | TCP/IP layer | Job | Matching OSI layers |
|---|---|---|---|
| 4 | **Application** | Applications and processes that use the network | 7 Application, 6 Presentation, 5 Session |
| 3 | **Host-to-Host Transport** | End-to-end data delivery between programs | 4 Transport |
| 2 | **Internet** | Defines the datagram (the IP packet) and routes it | 3 Network |
| 1 | **Network Access** | Routines for using the physical network | 2 Data Link, 1 Physical |

TCP/IP folds the top three OSI layers into one: an application handles its own presentation and sessions. It folds the bottom two into one too, because TCP/IP deliberately says nothing about the hardware. Any network that can carry an IP datagram will do.

You'll hear both models used at once. "Layer 2" and "layer 3" almost always mean OSI's data link and network layers, even when people are talking about TCP/IP networks. A **layer 2 switch** forwards frames by hardware address, and a **layer 3 switch** or router forwards packets by IP address.

## Where devices live

| Device | Layer | What it looks at |
|---|---|---|
| Hub, repeater, cable | 1 Physical | Nothing: it just repeats the signal |
| Switch, bridge, wireless access point | 2 Data Link | Hardware (MAC) addresses in the frame header |
| Router | 3 Network | IP addresses in the packet header |
| Firewall | 3 and 4, sometimes up to 7 | Addresses and ports, and sometimes the content |
| Your computer | All of them | It builds the whole stack to send, and unpacks it to receive |

Next, a check on the TCP/IP model, then a rapid-fire drill: name the layer.
