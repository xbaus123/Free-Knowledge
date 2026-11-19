# Latency, Bandwidth, and Round Trips

*Chapter 1 · Foundations.*

## Latency vs. throughput

Two numbers describe a network path, and they're independent:

- **Latency**: how long one bit, or one small message, takes to get there. Usually quoted as the **round-trip time (RTT)**: there and back.
- **Bandwidth**: how many bits per second the path can carry. **Throughput** is how much you actually achieve.

Think of a pipe: latency is its length, and bandwidth is its width. A wider pipe doesn't make water arrive sooner.

Where latency comes from:

- **Propagation**: light in fiber covers about 200,000 km/s, or 5 µs per kilometer. California to the Netherlands and back is about 150 ms, and no upgrade will ever change that.
- **Transmission**: pushing the bits onto the wire takes size ÷ bandwidth. 1 MB at 100 Mbit/s is 80 ms.
- **Queueing**: waiting in router and server queues. It's the part that varies, and it explodes near capacity (earlier in this chapter).
- **Processing**: the time the server spends on the request.

### Round trips are the real cost

Fetching a page over a **new** HTTPS connection takes:

1. 1 RTT for the TCP handshake,
2. 1 RTT for the TLS 1.3 handshake,
3. 1 RTT for the request and the first byte of the response,
4. plus the transmission time.

Across an ocean, that's about half a second before a large bandwidth makes any difference. So systems fight round trips: **connection pooling** and **keep-alive** reuse connections, **CDNs** move content closer to users (chapter 6), and protocols batch requests.

### The window caps throughput

TCP only lets a **window** of unacknowledged bytes be in flight, and acknowledgments take a round trip to come back. So:

> throughput ≤ window ÷ RTT

With a 64 KB window and a 100 ms RTT, that's about 5 Mbit/s, even on a 1 Gbit/s link. To keep a link full, the window must be at least the **bandwidth-delay product**: bandwidth × RTT, the amount of data "in the pipe" at any moment. For 1 Gbit/s and 100 ms, that's 12.5 MB.

Next, a short check on what you just read.
