# TCP and UDP

*Chapter 1 · Foundations.*

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

Even TCP can't make the network reliable, only *hide* most of its failures. If the other side vanishes, TCP eventually gives up, and your application sees a timeout. You'll spend chapter 7 on what that means.

Next, a short check on what you just read.
