# Subnet Masks and CIDR

*Chapter 4 · The Network Layer.*

Classes fixed the network/host split at 8, 16, or 24 bits. A **subnet mask** lets it fall anywhere. It's 32 bits, like an address: **1s over the network part, 0s over the host part**, always 1s first.

```
 address   10.104.216.118   00001010.01101000.11011000.01110110
 mask      255.255.252.0    11111111.11111111.11111100.00000000
                            └──────── 22 ones ───────┘└ 10 zeros ┘
```

## Prefix length (CIDR notation)

Counting the 1s gives the **prefix length**, written after a slash: `10.104.216.118/22`. Same information, shorter.

| Prefix | Mask | Host bits | Usable hosts |
|---|---|---|---|
| /8 | 255.0.0.0 | 24 | 16,777,214 |
| /16 | 255.255.0.0 | 16 | 65,534 |
| /22 | 255.255.252.0 | 10 | 1,022 |
| /24 | 255.255.255.0 | 8 | 254 |
| /26 | 255.255.255.192 | 6 | 62 |
| /30 | 255.255.255.252 | 2 | 2 |

A partial octet of a mask can only be one of these, since the 1s come first: **128, 192, 224, 240, 248, 252, 254, 255**. A mask like 255.255.0.255 is not valid.

## Finding the network: AND

To find which network an address is on, **AND** the address with the mask, bit by bit. Where the mask is 1 the address bit survives; where it's 0 the result is 0.

```
 216 = 11011000
 252 = 11111100
 AND = 11011000 = 216     →  network 10.104.216.0/22
```

## Reading a real ipconfig

Here's `ipconfig` on a campus WiFi network:

```
Wireless LAN adapter Wi-Fi:
   Connection-specific DNS Suffix  . : wireless.marshall.edu
   Link-local IPv6 Address . . . . . : fe80::792a:3b7b:8b7a:c71f%10
   IPv4 Address. . . . . . . . . . . : 10.104.216.118
   Subnet Mask . . . . . . . . . . . : 255.255.252.0
   Default Gateway . . . . . . . . . : 10.104.216.2
```

- **10.104.216.118**: a private (10.x) address, so the campus uses NAT at its edge.
- **255.255.252.0** is a **/22**: this WiFi subnet holds up to 1,022 devices, much more than a class C.
- **Default gateway 10.104.216.2**: the router for everything off this subnet. It must be on the same subnet as the host, and it is: 10.104.216.0/22.
- The **fe80::** address is IPv6 link-local, the IPv6 cousin of 169.254.

## Same subnet, or through the router?

Every time a host sends a packet, it makes one decision: **is the destination on my subnet?** It ANDs both addresses with its mask. Same network → send straight to that host (ARP for its MAC). Different → send to the **default gateway** (ARP for the router's MAC).

```
   10.1.1.0/24                                 10.1.2.0/24
 .20 .21 .22 .23 .24 ── .1 [ router ] .1 ── .35 .36 .37
```

10.1.1.20 talking to 10.1.1.24: same /24, direct. 10.1.1.20 talking to 10.1.2.35: different network, so the packet goes to 10.1.1.1, which forwards it out its other interface, 10.1.2.1. Note the router has an address **on each network**, and by convention it's often `.1`.

Next, a check on masks and prefixes.
