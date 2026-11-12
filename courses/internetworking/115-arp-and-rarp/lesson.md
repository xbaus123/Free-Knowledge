# ARP and RARP, Revisited

*Chapter 4 · The Network Layer.*

You met ARP in chapter 3. Now that you know about subnets, it's worth a second look, along with its forgotten twin, RARP.

## Which layer is ARP?

ARP is a bit of an odd one out. Its messages ride directly in Ethernet frames, with no IP header, which sounds like layer 2. But it exists only to serve **IP**, and it deals in **IP addresses**. This course's lectures count ARP as **layer 3**; some books call it "layer 2.5". What matters is what it does: **IP address in, MAC address out**.

## ARP and the subnet mask

Here's how the last few lessons fit together. Before sending a packet, a host:

1. ANDs the destination IP with its mask. **Same subnet?**
2. **Yes** → ARP for the **destination's** MAC.
3. **No** → ARP for the **default gateway's** MAC.

So a host's ARP cache only ever holds **neighbors**: hosts on its own subnet, and its gateway. You'll never find a web server's MAC address in it. Here's `arp -a` from the same campus WiFi:

```
% arp -a
? (10.104.232.1) at a4:4c:11:e5:b:40 on en0 ifscope [ethernet]
? (10.104.232.2) at 0:0:c:7:ac:1 on en0 ifscope [ethernet]
mdns.mcast.net (224.0.0.251) at 1:0:5e:0:0:fb on en0 ifscope permanent [ethernet]
```

The second entry is a familiar trick. `00:00:0c:07:ac:01` isn't a real NIC: `00:00:0c:07:ac:xx` is reserved for **HSRP**, Cisco's version of the VRRP you saw in chapter 3. Two routers share a virtual gateway address, so if one fails the other takes over and nobody's ARP cache has to change.

## RARP: the reverse

**Reverse ARP (RARP)** asks the opposite question: *"Here's my MAC address. What's my IP address?"*

| | ARP | RARP |
|---|---|---|
| Question | "Who has this IP? Tell me your MAC." | "Here's my MAC. What's my IP?" |
| Who broadcasts | A host that knows an IP address | A host that knows only its own MAC |
| Who answers | The host with that IP | A **RARP server** that must be on the network |
| Used today? | Constantly | Almost never |

RARP was built for **diskless workstations**: machines with no disk to store a configuration, which booted knowing only the MAC address burned into their NIC. It was replaced by BOOTP and then **DHCP**, which does the same job and much more.

One useful side effect: since a RARP server keeps a table of MAC addresses, it can **spot duplicate MACs**. Two hosts claiming the same MAC is a strong sign of **MAC spoofing**.

Next, a check on ARP and RARP.
