# Input Ports and the Switching Fabric

*Chapter 6 · Routing.*

Follow one packet into the router.

## The input port

```
 link ──▶ [ line termination ] ──▶ [ link layer ] ──▶ [ lookup, forwarding, queuing ] ──▶ fabric
           layer 1: bits in         layer 2: frame      layer 3: where does it go?
```

1. **Line termination** receives the bits off the wire (layer 1).
2. The **link layer** checks the frame and strips it (layer 2, Ethernet for example).
3. **Lookup**: the port reads the destination IP address and finds the output port in its copy of the forwarding table. This is **destination-based forwarding**, and it has to finish at **line rate**: as fast as packets arrive.

If packets arrive faster than the fabric can take them, they wait in an **input queue**.

## Three kinds of switching fabric

| Fabric | How it works | Limit |
|---|---|---|
| **Memory** | The CPU copies each packet into memory, then out to the output port | Two memory trips per packet; one packet at a time. Early routers worked like ordinary computers |
| **Bus** | The input port puts the packet on a shared bus; only the right output port takes it | One packet on the bus at a time, so the bus speed caps the whole router |
| **Crossbar** (interconnection network) | A grid of paths connecting every input to every output | Packets to **different** outputs cross at the same time |

A crossbar is what fast modern routers use: two packets headed for two different outputs don't wait for each other.

## Head-of-line blocking

Even a crossbar can't send two packets to the **same** output at once. One has to wait. Worse, anything queued **behind** the waiting packet waits too, even if its own output is free:

```
 input 1: [ to X ][ to Y ]   ← the to-Y packet is stuck behind the to-X packet
 input 2: [ to X ]           ← this one won the race to output X
```

That's **head-of-line (HOL) blocking**: the packet at the front of a queue holds up everything behind it.

Next, a check on the input side.
