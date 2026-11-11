# ARP: Seeing Layer 2

*Chapter 3 · The Data Link Layer.*

A host that wants to send an IP packet to a neighbor knows the neighbor's **IP address**. But the frame needs the neighbor's **MAC address**. The **Address Resolution Protocol (ARP)** connects the two.

## How ARP works

1. Host A wants to reach 192.168.1.1. It checks its **ARP cache** (a table of IP-to-MAC pairs it's already learned).
2. Not there? A broadcasts an **ARP request** to `ff:ff:ff:ff:ff:ff`: *"Who has 192.168.1.1? Tell 192.168.1.156."*
3. Every host on the LAN receives it. Only the one with that IP address answers, with a **unicast ARP reply**: *"192.168.1.1 is at 3c:bd:c5:40:77:61."*
4. A stores the answer in its cache, and entries expire after a while (minutes), so the cache stays current.

ARP messages travel directly in Ethernet frames (EtherType `0x0806`), with no IP header. ARP only works **within one LAN**: to reach a host on another network, a host ARPs for its **default gateway** (the router) instead, and the router takes it from there.

## The `arp -a` command

`arp -a` prints the ARP cache, and it's the easiest way to **see layer 2** on your own network. It works on macOS, Windows, and Linux (on Linux, `ip neigh` shows the same). Here's a cache from a home network on a Mac:

```
% arp -a
g3100.myfiosgateway.com (192.168.1.1) at 3c:bd:c5:40:77:61 on en0 ifscope [ethernet]
? (192.168.1.151) at da:47:5e:b3:f2:81 on en0 ifscope permanent [ethernet]
chars-air-2 (192.168.1.156) at 3c:22:fb:45:a4:85 on en0 ifscope [ethernet]
mac (192.168.1.159) at 9a:c3:43:ad:95:e3 on en0 ifscope [ethernet]
? (192.168.1.165) at d6:1b:bc:2d:ef:6f on en0 ifscope [ethernet]
kristenysiphone (192.168.1.166) at a6:ab:f1:8a:2f:9f on en0 ifscope [ethernet]
? (192.168.1.255) at ff:ff:ff:ff:ff:ff on en0 ifscope [ethernet]
mdns.mcast.net (224.0.0.251) at 1:0:5e:0:0:fb on en0 ifscope permanent [ethernet]
```

Each line is: name (or `?` if it has none), IP address, MAC address, interface (`en0`), and flags. Now read it with what you know:

- **192.168.1.1** is the gateway. Its OUI `3c:bd:c5` looks up as **Arcadyan**, a Taiwanese company that builds ISP routers.
- **3c:22:fb** is an **Apple** OUI: a MacBook Air.
- **da:47:...**, **9a:c3:...**, **d6:1b:...**, and **a6:ab:...** all **fail a vendor lookup**. That's not a mystery: their second hex digits are a, a, 6, and 6, so they're **locally administered**, private random addresses from phones and laptops.
- **192.168.1.255** maps to `ff:ff:ff:ff:ff:ff`: the subnet's broadcast IP goes to the Ethernet broadcast address.
- **224.0.0.251** (multicast DNS) maps to `1:0:5e:0:0:fb`, a multicast MAC. macOS drops leading zeros, so that's `01:00:5e:00:00:fb`.
- **permanent** means a static entry that doesn't expire.

A second example, from a campus network:

```
% arp -a
? (10.191.0.1) at 0:0:5e:0:1:33 on en0 ifscope [ethernet]
? (10.191.51.128) at dc:46:28:a1:60:26 on en0 ifscope [ethernet]
? (10.191.59.65) at 4c:77:cb:5e:88:d7 on en0 ifscope [ethernet]
? (10.191.106.26) at (incomplete) on en0 ifscope [ethernet]
? (10.191.127.255) at ff:ff:ff:ff:ff:ff on en0 ifscope [ethernet]
mdns.mcast.net (224.0.0.251) at 1:0:5e:0:0:fb on en0 ifscope permanent [ethernet]
```

- **dc:46:28** and **4c:77:cb** are **Intel** OUIs: laptops with Intel WiFi cards.
- **(incomplete)** means this host sent an ARP request for 10.191.106.26 and **got no reply**: that host is gone or not answering.
- The gateway's `00:00:5e:00:01:33` isn't a vendor's OUI either. `00:00:5e` belongs to IANA, and `00:00:5e:00:01:xx` is reserved for **VRRP**, a protocol that lets two or more routers share one virtual gateway address. If one router fails, the other takes over the same MAC, and nobody's ARP cache needs to change.

## ARP spoofing

ARP has **no authentication**. Any host can send a reply, even one nobody asked for, and most hosts will believe it. In **ARP spoofing** (or ARP poisoning), an attacker announces *"192.168.1.1 is at my MAC address"*. Victims then send their gateway traffic to the attacker, who can read or change it before passing it on: a **man-in-the-middle**.

Defenses include **dynamic ARP inspection** on switches (checking ARP replies against a trusted table), static ARP entries for critical hosts, and encryption, so intercepted traffic is unreadable anyway.

Next, a check on ARP.
