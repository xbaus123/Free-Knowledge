# IP Aliasing

*Chapter 4 · The Network Layer.*

One NIC usually has one IP address. But it doesn't have to. **IP aliasing** binds **several IP addresses to the same interface**, and so to the same **MAC address**.

```
          en0, MAC 3c:22:fb:45:a4:85
          ├── 192.168.1.156/24   (the main address, from DHCP)
          └── 192.168.1.15/24    (an alias, set statically)
```

To the rest of the network it looks like two hosts that happen to share a MAC address. ARP for either IP address and you get the same MAC.

## Why bother?

- **Several services, one machine**: a server can host two web sites, each on its own address.
- **Moving a server**: give the new address as an alias, switch everyone over, then drop the old one. No downtime.
- **Two logical networks on one wire**: a host on 10.1.1.0/24 with an alias on 10.1.2.0/24 can talk to both without a router.
- **Labs and testing**: practice routing, firewalls, or subnetting with one machine.

Aliases are **static** addresses: DHCP gives out one address per interface. An alias can have its own **subnet mask**, but keep its subnet no bigger than the network the physical interface is actually on.

## Adding an alias

Adding **192.168.1.15/24** to interface `en0`:

```
# macOS (and BSD)
sudo ifconfig en0 alias 192.168.1.15 netmask 255.255.255.0 up

# Linux
sudo ip addr add 192.168.1.15/24 dev en0
```

On Linux the interface is more often called `eth0` or `enp3s0`; `ip addr` lists them. To remove the alias: `sudo ifconfig en0 -alias 192.168.1.15` on macOS, `sudo ip addr del 192.168.1.15/24 dev en0` on Linux.

These commands only last **until the next reboot**. To make an alias permanent, put it in the OS's network configuration: on older Ubuntu `/etc/network/interfaces`, on newer Ubuntu a **netplan** file in `/etc/netplan/`. Check your OS's man pages.

## The catch

Every alias is another address to secure, monitor, and document. A forgotten alias is an open door that doesn't show up in DHCP records.

Next, a check on IP aliasing.
