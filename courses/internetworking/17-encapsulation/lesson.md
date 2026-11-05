# Encapsulation: Building a Frame by Hand

*Chapter 1 · Intro to Networks.*

When an application sends data, each layer on the way down wraps what it got from the layer above in its own **header**, and the data link layer adds a **trailer** too. That's **encapsulation**. On the receiving machine, each layer on the way up removes its own header (and trailer) and hands what's left to the layer above. That's **de-encapsulation**.

```
 Sending computer                                         Receiving computer
 ─────────────────                                        ──────────────────
 Application  ┐                                         ┌  Application
 Presentation ├─────────────────────── [Data]           ├  Presentation
 Session      ┘                                         └  Session
 Transport    ───────────────── [Segment hdr][Data] ───── Transport
 Network      ─────────── [Packet hdr][Segment hdr][Data] ─ Network
 Data Link    ─ [Frame hdr][Packet hdr][Segment hdr][Data][Frame trailer] ─ Data Link
 Physical     ─────────── 0101100110101010110001… ─────────── Physical
      │  encapsulation (down)                    de-encapsulation (up)  ▲
      ▼                                                                 │
```

Each layer only ever reads the header its partner layer wrote. The network layer on the receiver reads the packet header, and treats everything after it (segment header and data) as one opaque blob for the transport layer. That's what makes layers independent.

The data link layer is the only one that adds a trailer. It holds the **Frame Check Sequence (FCS)**: a checksum of the whole frame. If any bit was flipped on the wire, the receiver's checksum won't match, and the frame is thrown away.

## Your task

You'll build a tiny three-layer stack in Python using made-up but realistic headers. All numbers are **big-endian** ("network byte order"), which is what real Internet protocols use. Python's `struct` module does the packing: `struct.pack("!HH", 80, 443)` turns two numbers into 4 bytes, and `struct.unpack("!HH", data[:4])` turns them back. The `!` means network byte order, `H` is a 2-byte number, `I` is a 4-byte number, and `4s` / `6s` are 4 or 6 raw bytes.

### Transport layer: the segment

```
| src port (2) | dst port (2) | data length (2) | data ... |
```

- `transport_wrap(data, src_port, dst_port)` returns the segment as bytes.
- `transport_unwrap(segment)` returns `(src_port, dst_port, data)`.

### Network layer: the packet

```
| src IP (4) | dst IP (4) | payload length (2) | segment ... |
```

- `network_wrap(segment, src_ip, dst_ip)`: IPs are strings like `"10.0.0.1"`.
- `network_unwrap(packet)` returns `(src_ip, dst_ip, segment)`.

### Data link layer: the frame

```
| dst MAC (6) | src MAC (6) | payload length (2) | packet ... | FCS (4) |
```

Real Ethernet puts the *destination* first, so a switch can start deciding where to send a frame before the rest arrives. The FCS is `zlib.crc32` of everything before it (header and payload), the same CRC-32 algorithm Ethernet uses.

- `link_wrap(packet, src_mac, dst_mac)`: MACs are strings like `"aa:bb:cc:00:11:22"`.
- `link_unwrap(frame)` returns `(src_mac, dst_mac, packet)`.

### The physical layer, and the whole trip

- `to_bits(frame)` returns the frame as a string of `"0"` and `"1"`, 8 per byte, most significant bit first: `b"\x05"` becomes `"00000101"`.
- `from_bits(bits)` reverses it.
- `send(data, src, dst)` runs the whole stack down: transport, network, link, then bits. `src` and `dst` are dictionaries like `{"mac": "aa:bb:cc:00:11:22", "ip": "10.0.0.1", "port": 5000}`.
- `receive(bits)` runs it back up and returns a dictionary with the keys `data`, `src`, and `dst`, where `src` and `dst` have the same shape as above.

### When something's wrong

Every `unwrap` (and `from_bits`) must raise `ValueError` instead of returning garbage when:

- the input is shorter than the header (and trailer, for frames),
- the length field doesn't match how many bytes actually follow, or
- for frames, the FCS doesn't match: a bit was flipped in transit.

The starter file has helpers for converting IP and MAC addresses to and from bytes, so you can focus on the layering. Use **Run** to try things out, and **Submit** to run the tests.
