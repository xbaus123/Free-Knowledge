# UDP and TCP: A First Look

*Chapter 4 · The Network Layer.*

IP gets a packet to the right **host**. But a host runs many programs at once: a browser, a mail client, a game. The protocol field in the IP header says which **transport protocol** gets the data, and almost always it's one of two: **UDP** (17) or **TCP** (6). Strictly they're layer 4, but they're so tied to IP that you'll often hear the three (with ICMP) taught together. A later chapter goes deep; here's the first look.

## Ports

Both use **port numbers** to pick the right program on the host: web servers listen on port 80 (HTTP) and 443 (HTTPS), DNS on 53, DHCP on 67 and 68. An IP address plus a port is a **socket**, like a building's street address plus an apartment number.

## UDP: send it and move on

The **User Datagram Protocol** is **connectionless**, and so **stateless**: no setup, no memory of past packets. Its header is just **8 bytes**:

```
 0                16               31
┌─────────────────┬─────────────────┐
│   Source port   │ Destination port│
├─────────────────┼─────────────────┤
│     Length      │    Checksum     │
├─────────────────┴─────────────────┤
│               Data                │
└───────────────────────────────────┘
```

No acknowledgments, no retransmission, no ordering. It's **best effort**, which on a good network is pretty accurate. It shines in **fast, data-rich** traffic where a late packet is worthless anyway: video calls, live streaming, online games, and quick lookups like DNS and DHCP.

## TCP: a reliable connection

The **Transmission Control Protocol** is **connection-oriented**. Before any data flows, the two ends set up a connection, and TCP then guarantees the data arrives **complete and in order**, resending anything lost. That costs **more overhead**: a header of at least **20 bytes**:

```
┌─────────────────┬─────────────────┐
│   Source port   │ Destination port│
├─────────────────┴─────────────────┤
│          Sequence number          │
├───────────────────────────────────┤
│       Acknowledgment number       │
├──────┬────────┬───────┬───────────┤
│Offset│Reserved│ Flags │  Window   │
├──────┴────────┴───────┼───────────┤
│       Checksum        │  Urgent   │
├───────────────────────┴───────────┤
│        Options and padding        │
├───────────────────────────────────┤
│               Data                │
└───────────────────────────────────┘
```

**Sequence numbers** number every byte, so the receiver can put them in order. **Acknowledgment numbers** say *"I've got everything up to here"*. The **window** says how much more the receiver can take. The **flags** control the connection: **SYN** (start), **ACK** (acknowledge), **FIN** (finish), **RST** (reset).

## The three-way handshake

Every TCP connection starts the same way:

```
   client                                 server
     │ ──────────── SYN ────────────────▶ │   "Let's talk. My numbers start at x."
     │ ◀──────── SYN / ACK ────────────── │   "OK. Mine start at y. Got your x."
     │ ──────────── ACK ────────────────▶ │   "Got your y." Connection open.
```

Only after the third message does data flow. Web pages, email, file transfers, and SSH all ride on TCP, because a missing byte would break them.

| | UDP | TCP |
|---|---|---|
| Connection | None (connectionless, stateless) | Set up with a three-way handshake |
| Reliability | Best effort | Acknowledged, retransmitted, in order |
| Header | 8 bytes | 20+ bytes |
| Overhead | Low | Higher |
| Good for | Streaming, games, voice, DNS, DHCP | Web, email, file transfer, SSH |

Next, a check on UDP and TCP.
