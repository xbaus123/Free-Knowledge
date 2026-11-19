# Gorilla Compression

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

## Gorilla compression

A raw point takes 16 bytes: an 8-byte timestamp and an 8-byte float. Facebook's **Gorilla** paper (2015) compressed them to about **1.37 bytes per point** on its production data, using two observations.

**Timestamps are regular.** Scrapes happen every 15 seconds, so consecutive timestamps differ by 15, again and again. Store the first timestamp in full, then the first **delta** (the difference), then for each later point only the **delta of deltas**: how much this delta differs from the last one. A perfectly regular series is all zeros. A variable-length code then spends almost nothing on zeros and little on small jitter:

| Delta of deltas | Bits stored |
|---|---|
| 0 | 1 (`0`) |
| −63 to 64 | 2 + 7 (`10` and the value) |
| −255 to 256 | 3 + 9 (`110` and the value) |
| −2,047 to 2,048 | 4 + 12 (`1110` and the value) |
| Anything else | 4 + 32 (`1111` and the value) |

The first timestamp takes 64 bits and the first delta 14. After that, a steady series costs 1 bit per timestamp.

**Values change slowly.** XOR each value's 64-bit floating-point representation with the previous value's. If the value didn't change, the XOR is zero, stored as a single `0` bit. If it changed a little, the two floats share their sign, exponent, and leading mantissa bits, so the XOR has long runs of **leading and trailing zeros**. Gorilla stores only the count of leading zeros and the short run of meaningful bits in between, and reuses the previous point's run boundaries when they still fit. About half of Gorilla's values compressed to a single bit.

Both tricks need the points decoded **in sequence**, which is fine for range scans but rules out jumping to an arbitrary point. That's why chunks are small (around 120 points, or two hours): to read a point, decode its chunk from the start.

Next, a short check on what you just read.
