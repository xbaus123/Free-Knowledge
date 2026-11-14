# Output Port Queuing

*Chapter 6 · Routing.*

This is the most important part of the router to understand, because it's **where packets get delayed and lost**.

```
 fabric ──▶ [ buffer ▮▮▮▮▮▮ ] ──▶ [ link layer (send) ] ──▶ [ line termination ] ──▶ link, rate R
           (rate up to N × R)
```

## Why output ports need buffers

A router with **N** input ports can deliver packets to one output from all of them at once: up to **N × R** arriving, but the output link only sends at **R**. Until the burst passes, the extra packets sit in the output's **buffer**.

Buffers mean **delay** (queuing delay, from chapter 1's packet switching trade-off). And buffers are finite. When one fills up, the router has to throw something away. That's **loss due to congestion**.

## Drop policy: who gets thrown away?

| Policy | What it drops |
|---|---|
| **Tail drop** | The packet that just arrived, when the buffer is full. Simple, and the default |
| **Priority drop** | A lower-priority packet already in the buffer, to make room |
| **Random early detection (RED)** | A few random packets *before* the buffer fills, as a hint to TCP senders to slow down |

## Scheduling: who goes next?

The **scheduling discipline** picks which buffered packet is sent next. You met these in chapter 4: **FIFO**, **priority**, **round robin**, and **weighted fair queueing**.

Scheduling decides who gets the best performance, which makes it more than a technical question. **Network neutrality** is the policy debate over whether an ISP may prioritize, slow down, or charge for some traffic (say, its own video service) over others'.

Next, a check on output queuing.
