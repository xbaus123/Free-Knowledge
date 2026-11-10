# Twisted Pair: Shielded and Unshielded

*Chapter 2 · Topologies and the Physical Layer.*

The cable plugged into the back of almost every desktop computer is **twisted pair**: pairs of insulated copper wires twisted around each other, usually four pairs in one jacket, ending in an **RJ-45** plug.

## Why twist the wires?

Each pair carries one signal on two wires. Twisting them does two things:

- Outside noise hits both wires of a pair almost equally, so it cancels out when the receiver compares them. That's the cable's defense against **EMI** and **RFI**.
- Neighboring pairs are twisted at different rates, which keeps them from lining up and leaking into each other. That's the defense against **crosstalk**.

```
   ╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱╲╱    pair 1 (tight twist)
   ─╲─╱─╲─╱─╲─╱─╲─╱─╲─╱─╲─   pair 2 (looser twist)
```

Twisted-pair cable is sold in **categories**. Higher categories have tighter twists and better construction, so they support higher speeds: **Cat 5e** handles 1 Gbps, **Cat 6** handles 1 Gbps easily and 10 Gbps over short runs, and **Cat 6a** handles 10 Gbps over the full **100-meter** segment.

## Shielded twisted pair (STP)

**STP** wraps the pairs (or the whole bundle) in a metal foil or braid shield, like coax.

- **Protects from interference and crosstalk.**
- **Faster than unshielded**, because the cleaner signal supports higher speeds.
- **Expensive**.
- **Bulky**, and stiffer to bend.
- **Difficult to manufacture and install**: the shield has to be grounded properly at the ends, or it can make noise worse.

Use it where there's a lot of electrical noise: factories, hospitals, and near heavy machinery or power lines.

## Unshielded twisted pair (UTP)

**UTP** has no shield, just the twists.

- **Prone to crosstalk, RFI, and EMI**: the twisting helps, but there's nothing else.
- **Cheap**.
- **Most common**: nearly all office and home Ethernet is UTP.
- **Easy to install**: thin, flexible, and simple to terminate.

## STP vs UTP

| | Shielded (STP) | Unshielded (UTP) |
|---|---|---|
| Shield | Metal foil or braid | None |
| Noise resistance | Good | Prone to crosstalk, RFI, EMI |
| Speed | Faster | Slower |
| Cost | Expensive | Cheap |
| Handling | Bulky, hard to install | Thin, easy to install |
| Where you'll find it | Noisy industrial or medical sites | Almost every office and home |

Next, a check on twisted pair.
