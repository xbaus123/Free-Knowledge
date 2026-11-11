# Channel Partitioning: TDMA, FDMA, CDMA

*Chapter 3 · The Data Link Layer.*

Channel partitioning gives each node a **fixed, exclusive** share of the channel. No two nodes ever use the same share, so there are no collisions and no time wasted recovering from them. There are three ways to cut the channel up: by time, by frequency, or by code.

## TDMA: time division multiple access

Access to the channel goes in **rounds**. Each round is divided into slots, one per station, and each slot is exactly long enough to send one packet.

```
 example: 6 stations; 1, 3, and 4 have packets to send

 │◀────────── 6-slot frame ─────────▶│◀────────── 6-slot frame ─────────▶│
 │ [1] │     │ [3] │ [4] │     │     │ [1] │     │ [3] │ [4] │     │     │
   1     2     3     4     5     6     1     2     3     4     5     6
                    slots 2, 5, and 6 go idle
```

**Unused slots go idle.** Station 1 can't borrow station 2's slot, even if station 2 has nothing to send. With 6 stations, each one gets at most 1/6 of the channel's speed, however quiet the others are.

TDMA was used in 2G (GSM) cellular, where each call got a repeating time slot.

## FDMA: frequency division multiple access

The channel's **spectrum is divided into frequency bands**, and each station is assigned a fixed band. All stations transmit at the same time, each on its own frequency.

```
 frequency
    ▲  band 1 ████████████████████████  station 1 sending
    │  band 2 ────────────────────────  idle
    │  band 3 ████████████████████████  station 3 sending
    │  band 4 ████████████████████████  station 4 sending
    │  band 5 ────────────────────────  idle
    │  band 6 ────────────────────────  idle
    └──────────────────────────────────▶ time
```

**Unused bands go idle**, just like TDMA's unused slots. Radio and TV stations are FDMA: each has its own frequency. So is cable TV on a coax cable, where each channel occupies its own band.

## CDMA: code division multiple access

Every station transmits **at the same time, on the same frequencies**, but each one encodes its bits with its own unique **code** (a pattern of chips). The receiver uses the sender's code to pull that one signal out of the combined mix, and the other signals look like background noise.

The human analogy is a room full of pairs speaking different languages. Everyone talks at once, but if you only understand French, you can pick out the French conversation. CDMA was used in 3G cellular networks.

## Comparing them

| | Divides the channel by | Idle capacity |
|---|---|---|
| **TDMA** | Time slots | Unused slots go idle |
| **FDMA** | Frequency bands | Unused bands go idle |
| **CDMA** | Codes | Fewer active users means less interference, not idle slots |

Channel partitioning shines when traffic is **steady and predictable**, such as phone calls. It's wasteful for bursty computer traffic, for the same reason circuit switching was in Chapter 1.

Next, a check on TDMA, FDMA, and CDMA.
