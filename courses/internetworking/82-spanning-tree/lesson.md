# Spanning Tree Protocol

*Chapter 3 · The Data Link Layer.*

Good networks have **redundancy**: if one link or switch fails, there's another path. But on a switched LAN, a second path creates a **loop**, and Ethernet has no defense against loops.

## Why loops are a disaster

A broadcast frame arrives at a switch, which floods it out of every other port. If the switches are wired in a loop, each flooded copy comes back around and gets flooded again, and again. An Ethernet frame has no hop count or time-to-live, so the copies never die out. Within seconds:

- A **broadcast storm** uses up all the bandwidth on every link.
- Switches' **MAC tables thrash**: the same source MAC keeps arriving on different ports.
- The whole LAN stops working.

## What STP does

The **Spanning Tree Protocol (STP)**, IEEE 802.1D, lets you keep the redundant links while preventing loops:

- **Stops loops** by logically **blocking** just enough ports that the network is a tree: exactly one active path between any two switches.
- **Stops broadcast storms** as a result.
- **Keeps redundancy**: blocked ports are spares. If an active link fails, STP recalculates and unblocks one.

Switches run STP by exchanging small messages called **BPDUs** (bridge protocol data units).

## How it works

**1. Elect the root bridge.** Every switch has a **bridge ID** made of its **priority** (default **32768**) followed by its **MAC address**. The switch with the **lowest bridge ID** becomes the **root bridge**. Priority is compared first, and the MAC address only breaks ties. An administrator who wants a particular switch to be root gives it a lower priority.

**2. Find the best path.** Every other switch works out its cheapest path to the root. Each link has a **cost** based on its speed (faster is cheaper: classic values are 19 for 100 Mbps and 4 for 1 Gbps). The port on that cheapest path is the switch's **root port**.

**3. Block the extra ports.** On every link, one end is the **designated port**, the one that forwards toward that link. Any port that is neither a root port nor a designated port is **blocked**: it receives BPDUs but doesn't forward frames.

## An example

```
              SW1
         priority 32768
            MAC AAA
        Fa0/0 /   \ Fa1/0
             /     \
      Fa0/0 /       \ Fa0/0
          SW2 ───── SW3
  priority 32768   priority 32768
     MAC BBB         MAC CCC
         Fa1/0   Fa1/0
```

- All three priorities are 32768, so the **lowest MAC address** wins: **SW1 (AAA) is the root bridge**.
- SW2's root port is its **Fa0/0**, straight to SW1. SW3's root port is its **Fa0/0**, straight to SW1.
- Both of SW1's ports are designated (the root's ports always are).
- That leaves the SW2–SW3 link. One end must block. With equal costs to the root, the switch with the **lower bridge ID**, SW2 (BBB), gets the designated port, so **SW3's Fa1/0 is blocked**.

Frames between SW2 and SW3 now go via SW1. If the SW1–SW3 link fails, STP unblocks SW3's Fa1/0, and traffic flows again.

## Port states and roles

A port doesn't jump straight to forwarding: if it did, it could cause a loop before STP finished. It passes through states first:

| State | What the port does |
|---|---|
| **Blocking** | Listens to BPDUs only. Forwards nothing |
| **Listening** | Takes part in electing roles. Still forwards nothing and learns nothing |
| **Learning** | Starts **learning MAC addresses** into the table, but still doesn't forward |
| **Forwarding** | Fully active: sends and receives frames |

So a port must **listen, then learn, then forward**, before it transmits user traffic. The classic timers make that take 30 to 50 seconds, which is why **RSTP** (Rapid STP, 802.1w) was created: it converges in about a second.

The three port **roles** to remember: **root** (this switch's shortest path to the root bridge), **forward/designated** (forwards traffic onto its link), and **block** (the redundant spare).

Next, a check on spanning tree.
