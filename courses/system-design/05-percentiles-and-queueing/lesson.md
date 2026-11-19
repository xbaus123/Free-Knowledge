# Percentiles and Queueing

*Chapter 1 · Foundations.*

## Percentiles

The **mean** is a poor summary, because it doesn't tell you how many users actually experienced a delay. Use **percentiles** instead. Sort all response times from fastest to slowest:

- **p50** (the median): half of requests are faster than this. It's the typical experience.
- **p95, p99, p999**: 95%, 99%, or 99.9% of requests are faster. These measure **tail latency**.

If p99 is 1.5 seconds, 1 in 100 requests takes at least 1.5 seconds. That sounds rare, but tails matter for two reasons:

1. **Your best customers hit them most.** The users with the most data or the most activity tend to make the slowest requests. Amazon sets internal targets at p999 for exactly this reason.
2. **Tail latency amplification.** If one page load makes 10 backend calls in parallel, it's as slow as the *slowest* call. With 10 calls, about 10% of page loads hit at least one p99-slow call.

Targets on percentiles are written into **SLOs** (service level objectives, your internal goals) and **SLAs** (contracts that promise them to customers), for example "p99 below 200 ms, 99.9% of the time."

## Queueing: why latency explodes near capacity

A server can only work on so many requests at once. Once requests arrive faster than it can finish them, they **queue**. Every new arrival waits behind everyone already in line. Waiting time doesn't grow gently: past full utilization the queue grows without bound, and response times rise steeply with it. A few slow requests can also hold up the ones behind them. This is **head-of-line blocking**.

This is the most important intuition for the simulator: **watch utilization**. Around 70% busy, queues start forming in bursts. Near 100%, they run away.

Next, a short check on what you just read.
