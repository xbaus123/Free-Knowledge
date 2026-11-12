# Packet Scheduling

*Chapter 4 · The Network Layer.*

A router's output link can only send one packet at a time. When packets arrive faster than the link can send them, they wait in a **queue**. **Packet scheduling** decides which waiting packet goes next.

The simplest scheme is **first in, first out (FIFO)**: one queue, served in arrival order. It's fair in a naive way, but a big file download can fill the queue and make a video call stutter behind it. The three methods below fix that by sorting packets into **classes**, using any header field: the IP type of service byte, the protocol, a port number, a source address.

## 1. Priority scheduling

```
 high   [■ ■ ]──┐
 medium [■ ■ ■]─┼──▶ always serve the highest non-empty queue ──▶ link
 low    [■ ■ ■ ■]┘
```

Each class gets its own queue, ranked. The scheduler **always sends from the highest-priority queue that has packets waiting**. Voice traffic in the high queue never waits behind a download.

The catch: if high-priority traffic never stops, the low queue **starves** and never gets sent at all.

## 2. Round robin

```
 class A [■ ■ ■] ─┐
 class B [■    ] ─┼──▶ A, B, C, A, B, C, ... one packet each ──▶ link
 class C [■ ■  ] ─┘
```

The scheduler **cycles through the classes**, sending **one packet per class** per turn. An empty queue is skipped and the cycle continues. No class starves, but every class gets the same share, whether it needs it or not.

## 3. Weighted fair queueing (WFQ)

**Round robin with weights.** Each class gets a weight, and a share of the link in proportion to it. With weights 3, 2, and 1 on a 60 Mbps link:

| Class | Weight | Share | Guaranteed |
|---|---|---|---|
| Voice | 3 | 3/6 | 30 Mbps |
| Web | 2 | 2/6 | 20 Mbps |
| Backups | 1 | 1/6 | 10 Mbps |

That's a **minimum bandwidth guarantee** per class. If a class has nothing to send, its unused share goes to the others, so the link is never idle while anyone is waiting.

| Method | How it picks | Strength | Weakness |
|---|---|---|---|
| FIFO | Arrival order | Simple | No protection for urgent traffic |
| Priority | Highest class first | Urgent traffic never waits | Low classes can starve |
| Round robin | One packet per class, in turn | Nobody starves | Every class treated equally |
| WFQ | Round robin, weighted | Minimum bandwidth per class | More complex to configure |

Next, a check on packet scheduling.
