# Back-of-the-Envelope Estimation

Before drawing a single box, estimate. A few minutes of arithmetic tells you whether a design needs one server or a thousand, whether data fits in memory, and where the bottleneck will be. The goal is the right **order of magnitude**, not precision. Round aggressively.

## Handy numbers

**Time**

| Quantity | Rounded |
|---|---|
| Seconds in a day | 86,400 ≈ **10⁵** |
| Seconds in a month | ≈ 2.5 × 10⁶ |
| Seconds in a year | ≈ 3 × 10⁷ |

**Sizes**

| Prefix | Bytes |
|---|---|
| KB | 10³ (1,000) |
| MB | 10⁶ |
| GB | 10⁹ |
| TB | 10¹² |
| PB | 10¹⁵ |

One byte is 8 bits, so **1 GB/s ≈ 8 Gbit/s**. Network links are quoted in bits.

**Latency, roughly** (orders of magnitude matter, exact values vary by hardware)

| Operation | Time |
|---|---|
| Main memory reference | 100 ns |
| Read 1 MB sequentially from memory | 10–250 µs |
| SSD random read | 100 µs |
| Round trip within a data center | 0.5 ms |
| Read 1 MB sequentially from SSD | 1 ms |
| Spinning disk seek | 10 ms |
| Round trip California ↔ Europe | 150 ms |

## The method

1. **Users → requests/second.** Daily active users × actions per user ÷ 10⁵ seconds gives average requests/second.
2. **Average → peak.** Traffic isn't flat. Plan for peaks of 2–10× the average; 3× is a common assumption.
3. **Requests → bandwidth.** Multiply by the bytes each request moves.
4. **Writes → storage.** New bytes per day × retention.
5. **Capacity → machines.** Divide peak load by what one machine handles *at a safe utilization* (well under 100%), then add spares.

**Example:** 1M users each send 10 messages a day, about 1 KB each.

- 10⁷ messages/day ÷ 10⁵ s ≈ **100 messages/s** on average, so about 300/s at peak.
- 10⁷ × 1 KB = 10 GB of new data per day, or about **3.6 TB per year**.

Answer the questions on the right. Work them out on paper first; the options are deliberately far apart.
