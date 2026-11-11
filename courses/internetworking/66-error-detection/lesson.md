# Error Detection

*Chapter 3 · The Data Link Layer.*

Chapter 2 showed how signals get weaker (attenuation) and pick up noise along the way. Every so often, that's enough to flip a bit: a 1 arrives as a 0. The data link layer's job is to **notice**, and the tool is a few extra bits of redundancy.

## The idea

```
  sender                                         receiver
  ┌──────────────┬─────┐   bit-error-prone   ┌──────────────┬──────┐
  │      D       │ EDC │ ──────  link  ────▶ │      D'      │ EDC' │
  └──────────────┴─────┘                     └──────────────┴──────┘
                                              all bits in D' OK?
                                               yes → pass the datagram up
                                               no  → error detected: drop it
```

- **D** is the data being protected. It can include header fields as well as the payload.
- **EDC** is the **error detection and correction bits**, computed from D by the sender.
- The receiver gets **D'** and **EDC'**, which may differ from what was sent. It recomputes the check from D' and compares.

Two things to remember:

1. **Error detection is not 100% reliable.** If enough bits flip in just the wrong pattern, the damaged data can still pass the check. Good schemes make this very rare.
2. **A bigger EDC field detects (and corrects) more.** More redundant bits cost bandwidth but catch more kinds of error.

## Parity: the simplest check

Add **one parity bit** so the total number of 1s is even (*even parity*):

```
 data 0111000110101011  has nine 1s  →  parity bit 1  →  ten 1s, even ✓
```

Computing it is just **XOR** of all the bits: XOR is 1 when its inputs differ, so XOR-ing every bit together gives 1 exactly when there's an odd number of 1s.

If any **single** bit flips, the count of 1s becomes odd and the receiver knows something is wrong. But if **two** bits flip, the count is even again and the error slips through. Noise tends to come in **bursts** that hit several bits in a row, so one parity bit isn't enough for a real link.

**Two-dimensional parity** arranges the bits in a grid with a parity bit for each row *and* each column. A single flipped bit shows up as a bad row and a bad column, and where they cross is the bit to flip back. That's **error correction**: fixing the data without a retransmission.

## The Frame Check Sequence

Ethernet and WiFi use something far stronger than parity: a **cyclic redundancy check (CRC)**. Ethernet's is CRC-32, and its 32 bits travel in the last field of every frame, the **Frame Check Sequence (FCS)**:

```
 │ Dest MAC │ Src MAC │ Type │ Data … │ FCS │  ◀── computed over everything before it
```

The receiving NIC recomputes the CRC as the frame arrives. If it doesn't match the FCS, the frame is silently **dropped**. Ethernet doesn't ask for it again: higher layers (TCP, in Chapter 5) notice the missing data and resend it.

Next, a check on error detection.
