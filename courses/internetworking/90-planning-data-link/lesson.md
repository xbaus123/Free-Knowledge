# Planning the Data Link Layer

*Chapter 3 · The Data Link Layer.*

Chapter 2 ended with planning the physical layer. The class project continues one layer up: with the cables and rooms decided, how will frames move? Here are the questions to answer, with the reasoning for each.

## The questions

**1. Wired, wireless, or hybrid? Where are your access points?**
Most sites are a hybrid: wired for desks, servers, printers, and anything that needs speed or security; wireless for laptops, phones, and visitors. Place access points by **coverage**: walls, floors, and metal block radio, so plan for overlapping cells with no dead spots, and power them with PoE from the wiring closet switch.

**2. Who gets which access?**
Group users by what they need: staff, servers, guests, building systems like cameras and badge readers. Each group can become its own **VLAN**, with a router or firewall controlling what passes between them. Guests reach the internet and nothing else.

**3. What protocols will you use?**
**Ethernet** on the wire and **802.11 with WPA3** on the air. **STP** (or RSTP) on every switch, so redundant links don't turn into loops. **802.1Q** tagging on the links between switches to carry the VLANs. Keep an eye on **ARP**: dynamic ARP inspection against spoofing.

**4. What hardware will you use?**
- **Hubs**: no. They share one collision domain and repeat everything to everyone. They belong in a museum.
- **Switches vs bridges**: switches. A bridge only makes sense to join two existing segments cheaply; a switch gives every port its own collision domain, at line speed. Pick switches with **managed** features (VLANs, STP, MAC filtering, port security).
- Plus **access points**, **routers** at the edges between networks, and any **hypervisors** whose virtual switches are part of the LAN.

**5. VLANs vs physical LANs?**
Separate physical LANs (separate switches and cables for each group) give the strongest isolation, but cost more and are harder to change. **VLANs** split one set of switches into logical LANs: cheaper and flexible, since moving a user to another group is a configuration change rather than re-cabling. Most organizations use VLANs, and keep physical separation for the most sensitive systems.

## A worked example

A small office: 40 staff desks, 2 servers, a reception area for visitors, and security cameras.

| Decision | Choice |
|---|---|
| Access | Hybrid: wired desks and servers; 4 PoE ceiling access points |
| Groups | VLAN 10 staff, VLAN 20 servers, VLAN 30 guests, VLAN 40 cameras |
| Hardware | Two managed 48-port PoE switches, linked twice for redundancy; one router/firewall between VLANs |
| Protocols | Ethernet, 802.11 with WPA3, RSTP (one of the two links between switches blocks until it's needed), 802.1Q |
| Security | MAC filtering and port security on the switches, guest VLAN limited to the internet, dynamic ARP inspection |

Next, a check on planning the data link layer.
