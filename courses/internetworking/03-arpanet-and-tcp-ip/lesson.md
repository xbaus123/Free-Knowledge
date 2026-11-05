# ARPANET and the Birth of TCP/IP

*Chapter 1 · Intro to Networks.*

Packet switching was an idea. ARPANET was the network that proved it worked, and TCP/IP was the protocol that let separate networks join into one Internet.

## ARPANET

The Internet grew out of **ARPANET**, funded by the US Department of Defense's **DARPA** (then called ARPA, the Advanced Research Projects Agency). It ran from 1969 until it was shut down in 1990.

- **The first nodes (1969)** were UCLA, the Stanford Research Institute (SRI), UC Santa Barbara, and the University of Utah. Universities and government labs followed, including MIT and, across the Atlantic, University College London (UCL).
- **Interface Message Processors (IMPs)**, built by the company BBN, sat between each site's computer and the network. Each IMP received packets and forwarded them toward their destination, which makes it the ancestor of today's **router**.
- **A host-to-host protocol** let the computers at each end talk through the IMPs. It was designed by a group of UCLA graduate students in the Network Working Group, including **Steve Crocker**, **Jon Postel**, and **Vint Cerf**. Crocker wrote RFC 1 in 1969, and Postel went on to edit the RFC series for nearly 30 years.

### From ARPANET to TCP/IP

ARPANET's original protocol could only run across ARPANET itself. In 1974, **Vint Cerf** and **Bob Kahn** described a protocol that could carry data across *different* networks joined by gateways. It became **TCP/IP**.

- **1977**: TCP/IP carries traffic across three different networks (ARPANET, a packet radio network, and a satellite network) in one connected path.
- **1982**: the US Department of Defense adopts TCP/IP as its military networking standard.
- **January 1, 1983**: "flag day". Every ARPANET host switches to TCP/IP at once, and TCP/IP becomes the standard way to switch packets between networks. This is often called the Internet's birthday.

### Distributed by design

The Internet has **no central hub**. Routers forward packets based only on their own tables, and any router can learn a new path when an old one fails. There are big junction points, like Internet exchange points where many networks meet, but no single machine whose loss takes the whole network down.

Next, a short check on ARPANET and the road to TCP/IP.
