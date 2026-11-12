# Address Classes

*Chapter 4 · The Network Layer.*

In the original design of IPv4 (1981), the split between network and host was decided by the **first few bits** of the address. That gave five **classes**:

```
          0 1 2 3 4       8              16             24             31
Class A  │0│   netid      │                 hostid                      │
Class B  │1│0│        netid               │          hostid             │
Class C  │1│1│0│                netid                    │    hostid     │
Class D  │1│1│1│0│              multicast address                       │
Class E  │1│1│1│1│              reserved for future use                 │
```

## The classes at a glance

| Class | Leading bits | First octet | Network part | Host part | Default mask |
|---|---|---|---|---|---|
| **A** | `0` | 1–127 | 8 bits (1st octet) | 24 bits | 255.0.0.0 |
| **B** | `10` | 128–191 | 16 bits (1st–2nd) | 16 bits | 255.255.0.0 |
| **C** | `110` | 192–223 | 24 bits (1st–3rd) | 8 bits | 255.255.255.0 |
| **D** | `1110` | 224–239 | multicast groups | | |
| **E** | `1111` | 240–255 | reserved, experimental | | |

**You only need the first octet** to tell the class: 10.x.x.x is A, 172.16.x.x is B, 192.168.x.x is C, 224.0.0.251 is D.

The 127 network technically falls in class A's range, but it's reserved for **loopback** (next lesson), so usable class A networks are 1 to 126. Network 0 is reserved too.

## How big is each class?

The fewer bits for the network, the more for hosts:

| Class | Networks | Hosts per network |
|---|---|---|
| A | 126 | 2²⁴ − 2 = **16,777,214** |
| B | 2¹⁴ = **16,384** | 2¹⁶ − 2 = **65,534** |
| C | 2²¹ = **2,097,152** | 2⁸ − 2 = **254** |

Why **− 2**? In every network, two host IDs are reserved: **all 0s** is the address of the network itself, and **all 1s** is the network's **broadcast** address.

## Why classes went away

Classes were wasteful. A company with 300 hosts was too big for a class C (254 hosts), so it got a class B and left over 65,000 addresses unused. In **1993**, **CIDR** (Classless Inter-Domain Routing) replaced classes with a **prefix length** that can fall on any bit, which you'll meet in the subnet mask lesson. Classes are still everywhere in vocabulary, default masks, and exam questions, so they're worth knowing cold.

Next, a check on address classes.
