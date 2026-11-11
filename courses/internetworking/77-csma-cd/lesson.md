# CSMA and CSMA/CD: How Ethernet Shares a Wire

*Chapter 3 · The Data Link Layer.*

Slotted ALOHA transmits without checking whether anyone else is talking. That's rude, and wasteful. **CSMA** adds the obvious fix.

## CSMA: listen before you talk

**Carrier sense multiple access**: before transmitting, listen to the channel.

- **Channel sensed idle**: transmit the entire frame.
- **Channel sensed busy**: defer, and wait until it's quiet.

The human analogy: **don't interrupt others**.

## Collisions still happen

Listening first doesn't prevent every collision, because of **propagation delay**. A signal takes time to travel down the cable. Node A at one end starts sending at time t0. Node D at the far end listens at t1, slightly later, but A's signal hasn't reached it yet, so D hears silence and starts sending too.

```
 spatial layout:   A ─────────── B ─────────── C ─────────── D
 time  t0          A starts ───────────▶
   │   t1                                         ◀─────── D starts (it hasn't heard A yet)
   ▼                            ✗ the signals meet: collision
```

With plain CSMA, both nodes keep sending their whole frames anyway, so the **entire frame transmission time is wasted**. The longer the cable (and so the propagation delay), the bigger the window for this to happen: **distance and propagation delay determine the collision probability**.

## CSMA/CD: stop as soon as you notice

**CSMA with collision detection** adds one more rule: keep listening *while* you transmit. If what you hear on the wire isn't what you're sending, there's a collision, so **stop immediately**.

- Collisions are **detected within a short time**.
- Colliding transmissions are **aborted**, which **reduces the time wasted**.
- Collision detection is **easy on a wire** (compare the signal you send with the one on the cable) but **hard with wireless**, where your own transmission drowns out everything else at your antenna.

The human analogy: **the polite conversationalist**, who stops mid-sentence when someone else starts talking.

## The Ethernet CSMA/CD algorithm

1. The NIC receives a datagram from the network layer and **creates a frame**.
2. It **senses the channel**. If idle, it starts transmitting. If busy, it waits until the channel is idle, then transmits.
3. If the **entire frame** goes out without a collision: done!
4. If it detects another transmission while sending: **abort**, and send a short **jam signal** (48 bits) so every node knows there was a collision.
5. After aborting, enter **binary (exponential) backoff**:
   - After the **m**th collision in a row, pick **K at random from {0, 1, 2, ..., 2^m − 1}**.
   - Wait **K × 512 bit times**, then go back to step 2.
   - **More collisions mean a longer backoff interval**: the range of K doubles each time (Ethernet stops doubling after 10 collisions, and gives up after 16 attempts).

| Collision | K is chosen from | Longest wait |
|---|---|---|
| 1st | {0, 1} | 512 bit times |
| 2nd | {0, 1, 2, 3} | 3 × 512 |
| 3rd | {0, ..., 7} | 7 × 512 |
| 10th and later | {0, ..., 1023} | 1023 × 512 |

At 10 Mbps a bit time is 0.1 µs, so 512 bit times is 51.2 µs. Doubling the range adapts to load: with two nodes colliding, a small range sorts it out quickly; with many, the range quickly grows wide enough to spread them out.

**Why 512?** 512 bits is 64 bytes: Ethernet's **minimum frame size**. A frame has to be long enough that the sender is still transmitting when news of a collision from the far end of the cable gets back. Otherwise it would finish, assume success, and never know.

## CSMA/CA, and Ethernet today

Since WiFi can't detect collisions while transmitting, 802.11 uses **CSMA/CA (collision avoidance)** instead: wait a random time even when the channel is idle, and have the receiver send an **acknowledgment** for every frame. No ACK means assume a collision and retry.

Modern wired Ethernet is mostly **switched and full duplex**: every host has its own point-to-point link to a switch port, so there's nothing to collide with, and CSMA/CD sits unused. But the frame format, the 64-byte minimum, and the names all come from the shared-cable days.

Next, a check on CSMA and CSMA/CD.
