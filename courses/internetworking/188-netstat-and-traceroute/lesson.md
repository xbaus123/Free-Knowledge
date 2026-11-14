# Tools: netstat and traceroute

*Chapter 6 · Routing.*

Time to look at routing on a real machine. Open a terminal and try these as you read.

## Your routing table: `netstat -rn`

`netstat -rn` lists the host's routing table (`-r`) with numbers instead of names (`-n`). On a Mac:

```
$ netstat -rn
Internet:
Destination        Gateway            Flags     Netif
default            192.168.1.1        UGScg     en0
127.0.0.1          127.0.0.1          UH        lo0
192.168.1          link#6             UCS       en0
```

- The **default gateway** is usually listed **first**: `default` (or `0.0.0.0`) via 192.168.1.1. That's the basic algorithm's last step.
- `192.168.1` with `link#6` is the **directly connected** network: no gateway needed.
- Flags: **U** = up, **G** = goes through a gateway, **H** = a route to a single host.

On Linux the modern command is `ip route` (`default via 192.168.1.1 dev eth0`). On Windows, `route print`.

## Your connections: `netstat -an`

`netstat -an` shows **all** (`-a`) sockets that are open on the host:

```
$ netstat -an
Proto  Local Address         Foreign Address       State
tcp4   192.168.1.42.52814    142.250.80.46.443     ESTABLISHED
tcp4   *.22                  *.*                   LISTEN
udp4   *.5353                *.*
```

- **ESTABLISHED**: an open connection (here, to a web server on 443).
- **LISTEN**: a service waiting for connections (here, SSH on 22). An unexpected listener is a classic sign of something that shouldn't be there.
- macOS writes the port after a dot (`.443`); Linux and Windows use a colon (`:443`). On Linux, `ss -an` is the modern replacement.

## Every hop: `traceroute`

`traceroute` shows each router along the path. It uses the **TTL** field and **ICMP** from chapter 4:

1. Send a packet with **TTL 1**. The first router decrements it to 0, drops it, and sends back an **ICMP Time Exceeded**, revealing its address.
2. Send with TTL 2: the second router answers. And so on, until the destination replies.

```
$ traceroute example.com
 1  192.168.1.1     1.2 ms   1.0 ms   1.1 ms
 2  10.20.0.1       8.4 ms   8.1 ms   9.0 ms
 3  * * *
 4  203.0.113.9    14.2 ms  14.0 ms  13.9 ms
```

Three probes per hop, three round-trip times. **`* * *`** means no reply came back. traceroute used to be a great tool, but many networks now **block or rate-limit** the replies, so stars are common. (On Windows the command is `tracert`.)

Next, a check on these tools.
