# Special Addresses: Private, Loopback, NAT

*Chapter 4 · The Network Layer.*

Some addresses are set aside for special jobs. You'll see them every day.

## Private addresses (RFC 1918)

**RFC 1918** reserves three ranges for **private networks**:

| Range | Prefix | Class it sits in |
|---|---|---|
| 10.0.0.0 – 10.255.255.255 | 10.0.0.0/8 | one class A |
| 172.16.0.0 – 172.31.255.255 | 172.16.0.0/12 | 16 class Bs |
| 192.168.0.0 – 192.168.255.255 | 192.168.0.0/16 | 256 class Cs |

Anyone can use these, inside any home, school, or company, without asking permission. The catch: they're **non-routable** on the public Internet. Routers on the Internet drop packets addressed to them, since thousands of networks are using the very same addresses.

Watch the middle range: **172.16 to 172.31** only. 172.32.0.1 is an ordinary public address.

## NAT: getting private hosts online

So how does your laptop at 192.168.1.156 reach a web server? **Network Address Translation (NAT)**. A NAT router sits on the edge with **two (or more) network interfaces**: one on the private network, one with a **public** address.

```
 192.168.1.156 ──▶ ┌──────────────┐ ──▶ Internet
 192.168.1.159 ──▶ │  NAT router  │     (every packet now from 203.0.113.7)
 192.168.1.166 ──▶ │ inside │ outside
                   └──────────────┘
```

On the way out, it rewrites each packet's private source address to its own public one, and remembers the connection (by port number) in a table. When the reply comes back, it looks up the table and rewrites the destination back to the right private host. A whole house, or a whole campus, can share one public address. NAT is the main reason IPv4 survived running out of addresses in 2011.

Routers and **gateways** both do this kind of edge work. Your **default gateway** is the router your host sends everything to that isn't on its own network.

## Loopback: 127.0.0.1

The whole **127** network is reserved for **loopback**, and **127.0.0.1** (also called `localhost`) is the address everyone uses. A packet sent to it **never leaves the host**: the operating system turns it straight around.

That makes it a **testing and troubleshooting** tool. `ping 127.0.0.1` checks that the host's own network software works, without touching a cable or a NIC. If it fails, the problem is on this machine. Developers use it to run a server and a client on the same laptop. (This app's own engine listens on 127.0.0.1.)

## Two more you'll meet

- **169.254.x.x** is **link-local**. A host that asks for an address via DHCP and gets no answer gives itself one of these. Seeing 169.254 on a laptop usually means *"DHCP failed"*.
- **255.255.255.255** is the **limited broadcast**: every host on this LAN, never forwarded by a router. DHCP uses it.

Next, a check on special addresses.
