# Planning the Network Layer

*Chapter 4 · The Network Layer.*

The class project moves up another layer. Chapter 2 planned the cables and rooms, chapter 3 the switches and VLANs. Now: **addresses**. Here are the questions to answer, with the reasoning for each.

## The questions

**1. How many users, and how many devices?**
Count **devices**, not people. Each staff member might bring a laptop and a phone; add printers, cameras, access points, servers, and switch management interfaces. Then plan for **growth**: double it if you can.

**2. How many internal networks will you have?**
One subnet per **group that needs separating**: usually one per VLAN from chapter 3 (staff, servers, guests, cameras). Separate subnets let the router or firewall between them control exactly what talks to what, and keep each subnet's broadcasts to itself.

**3. How will you decide what goes on which network?**
By **function and trust**, not by where the desk happens to be. Servers together, guests isolated, building systems (cameras, badge readers) on their own. Ask: *"If this device were compromised, what else should it be unable to reach?"*

**4. What addressing scheme will you use?**
- **Private addresses** (RFC 1918) inside, with **NAT** at the edge. 10.0.0.0/8 gives the most room to grow.
- A **pattern people can read**: 10.*site*.*VLAN*.0/24, so 10.1.20.0/24 is site 1, VLAN 20.
- **Static** addresses for routers, servers, printers, and access points; **DHCP** for everything else. Reserve the bottom of each subnet for static devices, with the gateway at **.1**.

**5. What capacity do you need? What about traffic bursts?**
Size each subnet for its devices plus growth, using 2ʰ − 2. Size the **links** for the traffic: traffic is bursty, so plan for the busy hour, not the average. Where links are shared, use **packet scheduling** (WFQ or priority) so voice and video aren't stuck behind backups.

## A worked example

The small office from chapter 3: 40 staff, 2 servers, a reception area, cameras. Site number 1, private addressing, NAT at the firewall.

| VLAN | Purpose | Devices (with growth) | Subnet | Usable | Gateway | Addressing |
|---|---|---|---|---|---|---|
| 10 | Staff | ~100 (laptops + phones) | 10.1.10.0/24 | 254 | 10.1.10.1 | DHCP |
| 20 | Servers | 2 (room for 10) | 10.1.20.0/28 | 14 | 10.1.20.1 | Static |
| 30 | Guests | ~50 | 10.1.30.0/24 | 254 | 10.1.30.1 | DHCP, internet only |
| 40 | Cameras | 8 (room for 20) | 10.1.40.0/27 | 30 | 10.1.40.1 | Static, no internet |
| — | Router links | 2 | 10.1.255.0/30 | 2 | — | Static |

Every subnet has spare room, the third octet matches the VLAN number, and the guest and camera networks are fenced off by firewall rules at the router.

Next, a check on planning the network layer.
