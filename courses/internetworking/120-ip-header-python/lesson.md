# IP Headers and Ping in Python

*Chapter 4 · The Network Layer.*

Now build the packets from the last few lessons by hand: read an IPv4 header, check its checksum, forward it like a router does, and build the ICMP Echo Request that `ping` sends.

## The Internet checksum

IP, ICMP, UDP, and TCP all use the same simple checksum (RFC 1071):

1. Split the data into **16-bit words** (pairs of bytes, big-endian). If there's an odd byte at the end, pad it with a zero byte.
2. **Add** all the words.
3. Whenever the sum goes over 16 bits, **fold** the carry back in: `s = (s & 0xFFFF) + (s >> 16)`.
4. Take the **ones' complement**: `~s & 0xFFFF`.

The sender computes it with the checksum field set to 0, then writes the result in. The neat part: run the same checksum over a header **with** its correct checksum in place and you get **0**. That's how a receiver checks it.

## Unpacking bytes

`raw[8]` is the TTL byte (an `int`). Two bytes as a 16-bit number: `int.from_bytes(raw[2:4], "big")`. The first byte holds two 4-bit fields: `raw[0] >> 4` is the version, `raw[0] & 0x0F` is the IHL. The `struct` module works too, if you know it.

The IPv4 header, by byte offset:

| Bytes | Field |
|---|---|
| 0 | version (high 4 bits), IHL (low 4 bits) |
| 2–3 | total length |
| 4–5 | identification |
| 6–7 | flags (top 3 bits) and fragment offset (low 13 bits) |
| 8 | TTL |
| 9 | protocol |
| 10–11 | header checksum |
| 12–15 | source address |
| 16–19 | destination address |

## Your task

Implement these in the editor:

- `checksum(data)`: the Internet checksum of some bytes.
- `parse_header(raw)`: a dictionary of the header's fields (see the starter for the exact keys). The **flags** are bits in byte 6: `0x40` is DF and `0x20` is MF. The fragment offset counts 8-byte units, so return it **in bytes** (multiply by 8).
- `header_ok(raw)`: `True` if the header's checksum is right. Only check the header itself, `IHL × 4` bytes.
- `forward(raw)`: what a router does. Return a new copy with the TTL one lower and a freshly computed checksum, or `None` if the TTL would reach 0 (the router drops it, and sends an ICMP Time Exceeded). Leave the data after the header untouched.
- `echo_request(identifier, sequence, payload)`: the bytes of an ICMP Echo Request: type 8, code 0, checksum, identifier, sequence number, then the payload.

Use **Run** to try things out, and **Submit** to run the tests.
