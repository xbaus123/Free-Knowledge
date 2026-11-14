# Inside a Router

*Chapter 6 · Routing.*

Chapters 4 and 5 gave every network an address. This chapter is about **routing**: how a router decides where each packet goes next, how routers learn those decisions from each other, and how attackers try to bend them. We start inside the box itself.

## Routing vs forwarding

Two jobs, often mixed up:

- **Forwarding** is what a router does to **one packet**: read the destination address, look it up, push the packet out the right interface. It happens millions of times a second.
- **Routing** is how the router **builds the table** that forwarding looks things up in: talking to other routers, learning which networks are where, and picking the best paths.

An analogy: forwarding is taking the next exit on a road trip; routing is planning the whole route on a map before you leave.

## Two planes

A router is split into two halves that run at very different speeds:

```
            ┌───────────────────┐
            │ routing processor │   control plane: software, milliseconds
            └─────────┬─────────┘
 - - - - - - - - - - -│- - - - - - - - - - - - - - - - - - - - - - -
 input port ──▶ ┌─────┴─────┐ ──▶ output port
 input port ──▶ │ switching │ ──▶ output port   data plane: hardware, nanoseconds
 input port ──▶ │  fabric   │ ──▶ output port
                └───────────┘
```

| | Control plane | Data plane |
|---|---|---|
| Job | Routing: build the forwarding table | Forwarding: move each packet |
| Runs in | Software, on the routing processor | Hardware, in the ports and fabric |
| Speed | Milliseconds | Nanoseconds |
| Examples | Running OSPF or BGP, management (SSH, SNMP) | Table lookup, switching, queuing |

The routing processor hands its finished table down to the ports, so each port can forward on its own without asking the processor about every packet.

## The parts of the data plane

- **Input ports** receive the bits, strip the frame, and **look up** the destination in the forwarding table.
- The **switching fabric** moves the packet from the input port to the right output port.
- **Output ports** queue the packet, wrap it in a new frame, and send it on the link.

The next two readings walk through those, one side at a time.
