# Rules to Remember

*Chapter 5 · Subnetting in Practice.*

Before you start drawing subnet boundaries, a few rules that every working network follows.

## Static addresses for servers and printers

A **server** or a **printer** has to be found by everyone else. If its address changed every few days, every bookmark, print queue, and DNS record pointing at it would break. So servers, printers, routers, switches, and access points get **static** addresses: typed in by hand (or a DHCP *reservation* that always hands out the same one), and written down.

Keep those static addresses in a **known part of each subnet**, usually the bottom. For example: .1 to .20 static, .21 and up handed out by DHCP.

## Dynamic addresses need their own room, and care with the lease

DHCP hands out addresses from a **pool**, and each one comes with a **lease time** (its TTL): how long the client may keep it before it has to renew.

- The pool needs its **own range**, sized for the devices that will use it, and that range must **never overlap** the static addresses. If DHCP hands a laptop the printer's address, both break.
- Many organizations give dynamic devices a **subnet of their own**, such as one for guest WiFi.
- Pick the **lease time** for the subnet. On guest WiFi, people come and go every hour; with a week-long lease, the pool fills with addresses held by phones that left days ago, and new guests get nothing. Busy, short-stay subnets want **short leases** (an hour or a few). Stable office desktops can have long ones (a day or more).

## The router gets the first host address

By convention, the router (the **default gateway**) takes the **first usable address** in the subnet:

| Subnet | First usable (the router) | Hosts |
|---|---|---|
| 192.168.10.0/24 | 192.168.10.1 | .2 to .254 |
| 10.1.1.64/26 | 10.1.1.65 | .66 to .126 |
| 166.23.9.16/28 | 166.23.9.17 | .18 to .30 |

It's a convention, not a law (some sites use the last address), but pick one rule and stick to it so nobody has to look up the gateway.

## Robbing Peter to pay Paul

An IPv4 address is **always 32 bits**. You can't add more. Every bit you **borrow** for the subnet part is a bit the **host** part loses:

| Prefix | Subnet bits borrowed from a /24 | Subnets | Usable hosts each |
|---|---|---|---|
| /24 | 0 | 1 | 254 |
| /25 | 1 | 2 | 126 |
| /26 | 2 | 4 | 62 |
| /27 | 3 | 8 | 30 |
| /28 | 4 | 16 | 14 |

Each step **doubles the subnets and halves the hosts**. More subnets always means smaller subnets: you're robbing Peter (the host ID) to pay Paul (the network ID).

Next, a check on the rules.
