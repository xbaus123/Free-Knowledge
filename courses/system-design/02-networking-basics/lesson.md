# Networking Basics: Packets, Names, and Round Trips

*Part I · Foundations.*

Every arrow in a system diagram is a network call. When you draw "client → load balancer → server → database," each arrow hides addresses, routing, a handshake, possibly a DNS lookup, and at least one round trip. Most of the surprising behavior in distributed systems comes from those arrows: requests that are slow, lost, duplicated, or reordered. This lesson covers what happens inside one arrow.

## The layers

Networking is built as a stack. Each layer uses the one below it and hides its details from the one above:

| Layer | Job | Examples |
|---|---|---|
| Application | What the bytes mean | HTTP, DNS, gRPC, SMTP |
| Transport | Conversations between programs | TCP, UDP, QUIC |
| Network | Getting a packet from one machine to another, across networks | IP |
| Link | Moving frames across one physical hop | Ethernet, Wi-Fi |

Your code mostly lives at the top two layers. But the guarantees you get, and the ones you don't, come from the layers underneath.

## IP: addresses and best-effort delivery

The **Internet Protocol** gives every machine an **address** and moves **packets** (chunks of up to about 1,500 bytes) toward it, one **router** hop at a time. Each router looks at the destination address and forwards the packet to a neighbor that's closer.

An **IPv4 address** is a 32-bit number, written as four bytes in decimal: `192.168.1.10` is `192·256³ + 168·256² + 1·256 + 10`. Four billion addresses ran out long ago, so **IPv6** uses 128 bits (`2001:db8::1`), and many networks share one public IPv4 address behind **NAT**.

Addresses are handed out in blocks written in **CIDR** notation: `10.0.0.0/8` means "every address whose first 8 bits match `10.0.0.0`," which is 2²⁴ ≈ 16.7 million addresses. A `/24` has 256 addresses, and a `/32` is one address. Routers and firewalls use these blocks constantly ("send `10.0.0.0/8` this way," "allow traffic from `172.16.0.0/12`"). Three blocks are **private**, reserved for internal networks and never routed on the public internet: `10.0.0.0/8`, `172.16.0.0/12`, and `192.168.0.0/16`. Your cloud servers almost certainly live in one of them.

The crucial property: **IP is best-effort**. A packet may be:

- **dropped** (a router's queue was full, a link flapped),
- **duplicated** (a retry somewhere below),
- **reordered** (two packets took different paths),
- **delayed** by an unbounded amount.

IP doesn't tell you which. Everything reliable is built on top of this unreliable base.

## TCP and UDP: two ways to use IP

**Ports** let many programs share one address: a web server listens on port 443, a database on 5432. A connection is identified by both ends' address and port.

### TCP: a reliable byte stream

**TCP** turns unreliable packets into a reliable, ordered **stream of bytes**:

- **Connection setup**: a **three-way handshake** (SYN, SYN-ACK, ACK) costs one round trip before any data flows.
- **Sequence numbers**: every byte has a number. The sender splits the stream into **segments**, each labeled with the number of its first byte.
- **Acknowledgments**: the receiver replies with a **cumulative ACK**, the number of the next byte it's waiting for. "ACK 1000" means "I have everything before byte 1000."
- **Retransmission**: if an ACK doesn't arrive in time, the sender resends. The receiver may then see the same bytes twice, and must drop the duplicates.
- **Ordering**: segments that arrive early wait in a buffer until the gap before them is filled. Then they're delivered in order.
- **Flow and congestion control**: the sender keeps at most a **window** of unacknowledged bytes in flight, so it doesn't overwhelm the receiver or the network. The window grows while things go well and shrinks sharply on packet loss.

The price is **head-of-line blocking**: one lost segment stalls every byte behind it until the retransmission arrives, even if those bytes are already sitting in the receiver's buffer.

### UDP: datagrams, nothing more

**UDP** sends individual **datagrams** with a port number and a checksum, and nothing else: no connection, no ordering, no retransmission. That sounds worse, but it's exactly right when:

- **Late data is useless**: a video call or a multiplayer game would rather skip a lost frame than wait for it.
- **The exchange is one small request and one small response**: a classic DNS query fits in one packet each way, so a handshake would double the cost.
- **You want your own reliability rules**: **QUIC** (the transport under HTTP/3) is built on UDP. It does its own retransmission, but per stream, so one lost packet doesn't block unrelated streams.

| | TCP | UDP |
|---|---|---|
| Setup | Handshake (1 RTT) | None |
| Delivery | Reliable, ordered, no duplicates | Best effort |
| Unit | Byte stream | Individual datagrams |
| Congestion control | Built in | Up to the application |
| Typical uses | HTTP/1.1 and HTTP/2, databases, SSH | DNS, video and voice, games, QUIC |

Even TCP can't make the network reliable, only *hide* most of its failures. If the other side vanishes, TCP eventually gives up, and your application sees a timeout. You'll spend lesson 26 on what that means.

## DNS: names to addresses

People and config files use names like `api.example.com`. The **Domain Name System** turns them into addresses. It's a distributed, hierarchical, heavily cached database:

1. Your machine asks a **recursive resolver** (run by your ISP, your cloud provider, or `8.8.8.8`).
2. If the resolver has nothing cached, it asks a **root server**: "where is `api.example.com`?" The root doesn't know, but it **refers** the resolver to the servers for `com`.
3. The `com` servers refer it to the **authoritative servers** for `example.com`.
4. The authoritative server answers with the record.

Common record types:

| Type | Meaning |
|---|---|
| `A` / `AAAA` | The name's IPv4 / IPv6 address |
| `CNAME` | An alias: "this name is really that name" (look that one up instead) |
| `NS` | Which servers are authoritative for a zone (the referrals above) |
| `MX` | Where to deliver mail for the domain |

Every record carries a **TTL** (time to live, in seconds). Resolvers cache answers *and* referrals until their TTL runs out, which is why most lookups never leave the resolver, and why the root servers aren't buried under the internet's traffic.

TTLs are a design decision:

- **Long TTLs** (hours): fewer lookups, faster responses, but a change (moving to a new server, failing over to another region) takes hours to reach everyone.
- **Short TTLs** (30 to 60 seconds): fast failover and **DNS-based load balancing** (return different addresses to different clients), at the cost of more lookups.

## Latency vs. throughput

Two numbers describe a network path, and they're independent:

- **Latency**: how long one bit, or one small message, takes to get there. Usually quoted as the **round-trip time (RTT)**: there and back.
- **Bandwidth**: how many bits per second the path can carry. **Throughput** is how much you actually achieve.

Think of a pipe: latency is its length, and bandwidth is its width. A wider pipe doesn't make water arrive sooner.

Where latency comes from:

- **Propagation**: light in fiber covers about 200,000 km/s, or 5 µs per kilometer. California to the Netherlands and back is about 150 ms, and no upgrade will ever change that.
- **Transmission**: pushing the bits onto the wire takes size ÷ bandwidth. 1 MB at 100 Mbit/s is 80 ms.
- **Queueing**: waiting in router and server queues. It's the part that varies, and it explodes near capacity (lesson 1).
- **Processing**: the time the server spends on the request.

### Round trips are the real cost

Fetching a page over a **new** HTTPS connection takes:

1. 1 RTT for the TCP handshake,
2. 1 RTT for the TLS 1.3 handshake,
3. 1 RTT for the request and the first byte of the response,
4. plus the transmission time.

Across an ocean, that's about half a second before a large bandwidth makes any difference. So systems fight round trips: **connection pooling** and **keep-alive** reuse connections, **CDNs** move content closer to users (lessons 19 and 23), and protocols batch requests.

### The window caps throughput

TCP only lets a **window** of unacknowledged bytes be in flight, and acknowledgments take a round trip to come back. So:

> throughput ≤ window ÷ RTT

With a 64 KB window and a 100 ms RTT, that's about 5 Mbit/s, even on a 1 Gbit/s link. To keep a link full, the window must be at least the **bandwidth-delay product**: bandwidth × RTT, the amount of data "in the pipe" at any moment. For 1 Gbit/s and 100 ms, that's 12.5 MB.

## Your task

`solution.py` has four independent parts. The tests check each one separately.

### 1. IP addresses

- `ip_to_int(address)`: `"192.168.1.10"` → `3232235786`. Raise `ValueError` for anything that isn't four numbers from 0 to 255 separated by dots.
- `in_subnet(address, cidr)`: is the address inside the block? Build a mask with the first *n* bits set and compare the masked addresses.

```python
(0xFFFFFFFF << (32 - 8)) & 0xFFFFFFFF   # the /8 mask: 0xFF000000
```

### 2. TCP's receive side

`Receiver.receive(seq, payload)` gets one segment. `seq` is the number of its first byte, starting at 0. Segments arrive late, twice, out of order, and sometimes overlapping a previous one (a retransmission that combined two segments). Append every byte you can to `self.data` in order, hold early segments until the gap before them is filled, skip bytes you already have, and return the cumulative ACK: `len(self.data)`.

### 3. A caching DNS resolver

`Resolver(network).resolve(name, now)` returns the name's IPv4 address, or `None`. `network.query(server, name)` asks one server about one name and returns an `A` answer, a `CNAME` alias, an `NS` referral (`{"type": "NS", "zone": "com", "value": "tld-com", "ttl": 172800}` means "ask server `tld-com`, which knows names in `com`"), or `None` for "no such name."

- Without a cache, start at the server `"root"` and follow referrals.
- For a `CNAME`, resolve its target the same way.
- Cache `A` and `CNAME` answers by name, and referrals by zone, until `now + ttl`. At exactly that time they've expired.
- Start each lookup at the server for the **longest** cached zone that contains the name: `www.example.com` is in `example.com` and in `com`, and `example.com` is in its own zone too.

The tests count every query your resolver sends.

### 4. Latency and throughput

- `transfer_ms(size_bytes, bandwidth_mbps, rtt_ms, new_connection=True, tls=False)`: round trips (request, plus the TCP handshake and the TLS handshake on a new connection) times the RTT, plus transmission time. 1 Mbit/s is 1,000,000 bits per second.
- `max_throughput_mbps(window_bytes, rtt_ms)`: window ÷ RTT, in Mbit/s.
- `bandwidth_delay_product(bandwidth_mbps, rtt_ms)`: in bytes.

Use the **Scratchpad** to play with the numbers: how much faster does a 2 KB API call get if you double the bandwidth? If you halve the RTT?

## Key terms

| Term | Meaning |
|---|---|
| Packet | A chunk of data IP delivers on a best-effort basis |
| CIDR block | A range of addresses sharing their first *n* bits, written `10.0.0.0/8` |
| TCP | A reliable, ordered byte stream over IP, with a handshake and retransmission |
| UDP | Individual datagrams with no delivery guarantees |
| Cumulative ACK | "I have every byte before this one" |
| Head-of-line blocking | One lost or slow item holding up everything behind it |
| DNS | The distributed, cached system that maps names to records |
| TTL | How long a cached record stays valid |
| RTT | Round-trip time: there and back |
| Bandwidth-delay product | Bandwidth × RTT: the data in flight on a full link |

Next, you'll go inside one machine: processes, threads, locks, and why memory is fast and disks are slow.
