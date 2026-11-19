# Networking Basics: Packets, Names, and Round Trips

*Chapter 1 · Foundations.*

Time to build the pieces from the last four readings: IP address math, TCP's receive side, a caching DNS resolver, and the latency arithmetic.

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
