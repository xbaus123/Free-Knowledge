# ICMP and Ping

*Chapter 4 · The Network Layer.*

IP is a best-effort protocol: it sends packets and hopes. When something goes wrong, who tells the sender? The **Internet Control Message Protocol (ICMP)**.

## What ICMP does

- It **reports** errors. It **does not correct** them: fixing things is up to the sender.
- Reports go back to the packet's **source**, since that's the one address every packet carries.
- It was designed for routers to report problems, but every host uses it.
- ICMP messages travel inside IP datagrams (**protocol number 1**), so they're part of the network layer.

## The message types you need

Every ICMP message starts with a **type** number. The ones that matter most:

| Type | Meaning | When you see it |
|---|---|---|
| **0** | Echo Reply | The answer to a ping |
| **3** | Destination Unreachable | No route to the network, the host is down, or the port is closed |
| **5** | Redirect | A router telling a host *"use that other router, it's a better route"* |
| **8** | Echo Request | A ping |
| **11** | Time Exceeded | A packet's **TTL hit 0**, so a router dropped it. `traceroute` depends on this |
| **12** | Parameter Problem | Something in the IP header is malformed |

(Type 4, Source Quench, once told senders to slow down. It's been retired.)

## Ping

`ping` sends **Echo Requests** (type 8) and waits for **Echo Replies** (type 0). It tells you whether a host is reachable and how long the **round trip** takes.

```
$ ping 10.104.232.1
PING 10.104.232.1 (10.104.232.1): 56 data bytes
64 bytes from 10.104.232.1: icmp_seq=0 ttl=255 time=5.312 ms
64 bytes from 10.104.232.1: icmp_seq=1 ttl=255 time=9.583 ms
64 bytes from 10.104.232.1: icmp_seq=2 ttl=255 time=9.639 ms
64 bytes from 10.104.232.1: icmp_seq=3 ttl=255 time=10.547 ms
64 bytes from 10.104.232.1: icmp_seq=4 ttl=255 time=9.997 ms
64 bytes from 10.104.232.1: icmp_seq=5 ttl=255 time=8.661 ms
64 bytes from 10.104.232.1: icmp_seq=6 ttl=255 time=8.727 ms
64 bytes from 10.104.232.1: icmp_seq=7 ttl=255 time=3.475 ms
^C
--- 10.104.232.1 ping statistics ---
8 packets transmitted, 8 packets received, 0.0% packet loss
round-trip min/avg/max/stddev = 3.475/8.243/10.547/2.342 ms
```

Reading it:

- **56 data bytes** + the 8-byte ICMP header = **64 bytes** per reply.
- **icmp_seq** counts the pings. A gap in the numbers means one was lost.
- **ttl** is the TTL left in the reply. Operating systems start at different values: **64** for macOS and Linux, **128** for Windows, **255** for many routers. So ttl=255 here hints this is a router, zero hops away.
- **time** is the round trip. The **statistics** at the end summarize loss and timing.

Windows prints it differently, by default 4 pings of 32 bytes: `Reply from 192.168.86.1: bytes=32 time<1ms TTL=64`. When no reply comes back in time, it prints **Request timed out**.

## Ping as a troubleshooting ladder

Work outward, and the first step that fails tells you where the problem is:

1. `ping 127.0.0.1`: is this host's network software working?
2. `ping` your own IP address: is the NIC configured?
3. `ping` the default gateway: is the local network working?
4. `ping` something beyond it, like a public server: is routing and the Internet connection working?

One caution: plenty of hosts and firewalls **block ICMP** on purpose. No reply means *"no reply"*, not always *"host is down"*.

Next, a check on ICMP.
