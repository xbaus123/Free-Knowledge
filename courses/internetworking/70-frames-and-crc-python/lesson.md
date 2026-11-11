# Frames and CRC in Python

*Chapter 3 · The Data Link Layer.*

Time to build the error detection a NIC does in hardware. Part 1 works on bit strings, like the examples you did by hand. Part 2 builds and checks real Ethernet II frames, byte for byte.

## Part 1: parity and CRC

Bit strings are Python strings of `'0'` and `'1'`, such as `"101110"`. XOR of two bits is `int(a) ^ int(b)`.

The CRC is long division where every subtraction is XOR:

1. Append r zeros to the data, where r = `len(generator) - 1`.
2. Walk along the bits from the left. Wherever the current bit is 1, XOR the generator into the bits starting there. (Where it's 0, do nothing.)
3. Stop after the last data bit. The final r bits are the remainder **R**.

`crc_remainder("101110", "1001")` should give `"011"`, the reading's worked example.

## Part 2: Ethernet II frames

```
 │ dst 6 │ src 6 │ type 2 │ payload 46–1500 │ FCS 4 │
```

- MAC addresses arrive as text like `"3c:bd:c5:40:77:61"`: `bytes.fromhex(mac.replace(":", ""))` turns one into its 6 bytes.
- The EtherType is a 2-byte, big-endian number: `ethertype.to_bytes(2, "big")`.
- Pad the payload to 46 bytes with zero bytes: `bytes(n)` is n zero bytes.
- Ethernet's FCS is the standard CRC-32, which Python's `zlib.crc32` computes. It goes on the wire low byte first: `zlib.crc32(body).to_bytes(4, "little")`.

## Your task

Implement these functions in the editor:

- `parity_bit(bits)`: the even parity bit, `"0"` or `"1"`. Raise `ValueError` if `bits` has anything other than 0s and 1s.
- `crc_remainder(data, generator)`: the r CRC bits as a string, keeping leading zeros. Raise `ValueError` for a non-bit string, or a generator shorter than 2 bits or not starting with `1`.
- `crc_encode(data, generator)`: data followed by its CRC bits.
- `crc_check(codeword, generator)`: `True` if the codeword's remainder is all zeros.
- `build_frame(dst, src, ethertype, payload)`: the frame as `bytes`, padded, with its FCS. Raise `ValueError` if the payload is over 1500 bytes.
- `parse_frame(frame)`: a dictionary with `"dst"`, `"src"` (as lowercase colon text), `"ethertype"` (an int), `"payload"` (the bytes between the header and the FCS), and `"fcs_ok"` (whether the FCS matches). Raise `ValueError` for a runt under 64 bytes or a frame over 1518.

Use **Run** to try things out, and **Submit** to run the tests.
