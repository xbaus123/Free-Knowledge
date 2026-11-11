# Hubs, Bridges, and Switches

*Chapter 3 · The Data Link Layer.*

Collisions on a shared cable were the biggest problem with early Ethernet. Bridges and then switches solved it by **splitting the LAN into pieces** and forwarding each frame only where it needs to go.

## Hubs: everyone hears everything

A **hub** is a layer 1 device: a multiport repeater. A signal arriving on one port is copied out of **every other port**. It never reads the frame, so it can't know where it's going. Every host on a hub shares one **collision domain**: only one can transmit at a time, and the more hosts, the more collisions.

## Bridges

A **bridge** is a layer 2 device that **joins separate LAN segments**:

- It reads each frame's **destination MAC address** and only passes it across to the other segment if the destination is over there. Traffic that stays on one side, stays on one side.
- Each segment is now its **own collision domain**.
- Bridges run **minimal software** and usually have only a few ports.
- A bridge only knows about MAC addresses on the segments it connects. To move traffic **beyond its interfaces**, to another network, it needs a **router**.
- **MAC filtering is recommended**, so only known devices can send across it.

## Switches

A **switch** is a bridge with many ports, doing its forwarding in fast dedicated hardware. It has **greater capacity and is more scalable** than a bridge, and it has replaced both hubs and bridges in practically every LAN.

- **Every port is its own segment.** A host on a switch port has a private, full-duplex link. No shared medium means no collisions.
- The switch keeps a **MAC address table** (also called the CAM table, or forwarding table): which MAC address is reachable through which port.
- A switch **only sees what's attached to it**. Like a bridge, it connects to a **router** for delivery beyond the LAN.
- **MAC filtering is highly recommended**, and so is **encryption** for sensitive traffic, such as L2TP over IPsec, because anyone who can reach a switch port can try to read or inject frames.

## How a switch learns

Nobody types in the MAC address table: the switch **learns it** from the traffic itself. For every frame that arrives:

1. **Learn**: note the frame's **source MAC** and the port it came in on. Now the switch knows where that host is.
2. **Look up** the **destination MAC**:
   - **Known**, on a different port: **forward** the frame out of that one port only.
   - **Known**, on the **same** port it came in on: **filter** it (drop it), because the destination already heard it.
   - **Unknown**, or the broadcast address `ff:ff:ff:ff:ff:ff`: **flood** it out of every port except the one it came in on.

```
 Host A (port 1) sends to Host C, and the table is empty:
   learn  A → port 1
   C is unknown → flood out of ports 2, 3, 4

 Host C (port 3) replies to A:
   learn  C → port 3
   A is known → forward out of port 1 only
```

Entries **age out** after a few minutes of silence (often 300 seconds), so a host that moves to another port is relearned.

## Broadcast domains and VLANs

A switch separates **collision domains**, but a broadcast still goes out of every port: the whole switched LAN is one **broadcast domain**. A router separates broadcast domains.

A **VLAN (virtual LAN)** splits one physical switch into several logical LANs, each its own broadcast domain. Ports in VLAN 10 (say, staff) can't exchange frames with ports in VLAN 20 (guests) without going through a router. When VLANs span several switches, frames on the links between them carry a 4-byte **802.1Q tag** with the VLAN ID.

| | Layer | Reads MAC addresses? | Collision domains | Broadcast domains |
|---|---|---|---|---|
| **Hub** | 1 | No | One, shared by every port | One |
| **Bridge** | 2 | Yes | One per segment | One |
| **Switch** | 2 | Yes | One per port | One (or one per VLAN) |
| **Router** | 3 | Yes, and IP addresses | One per port | One per port |

Next, a check on hubs, bridges, and switches.
