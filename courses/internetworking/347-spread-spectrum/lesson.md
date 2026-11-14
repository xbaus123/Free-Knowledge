# Spread Spectrum: DSSS and FHSS

*Chapter 11 · Wireless and IoT.*

A narrow radio signal on one frequency is easy to jam and easy to listen to. **Spread spectrum** spreads the signal across a much wider band than it strictly needs, using a **code** that both ends know. Because it changes the physical signal itself, spread spectrum is a **layer 1** technique.

There are two main ways to do it.

## DSSS: direct sequence

**Direct Sequence Spread Spectrum** replaces every data bit with a fast pattern of **chips**, called the **chipping code**. Early Wi-Fi (802.11 and 802.11b) used the 11-chip **Barker code**:

```
 data bit 1  ->  1 0 1 1 0 1 1 1 0 0 0    (the Barker code)
 data bit 0  ->  0 1 0 0 1 0 0 0 1 1 1    (the code, inverted)
```

Eleven chips for every bit makes the signal about eleven times wider, so it fills **one wide channel**. In return:

- **Noise is survivable.** If a burst of noise flips a few chips, the rest still look much more like one pattern than the other, so the receiver recovers the bit.
- **Narrow interference** only hits a small slice of the wide signal.

**CDMA** cellular, from chapter 3, is built on the same idea: each user gets their own spreading code, so many users can share one band at the same time. Zigbee, later in this chapter, also uses direct sequence.

## FHSS: frequency hopping

**Frequency Hopping Spread Spectrum** sends on a narrow channel, but **hops** to a different channel many times a second, in a pseudo-random order. Both ends generate the same hop sequence from a shared starting value, so they hop together.

- **Harder to steal.** An eavesdropper without the sequence hears only fragments as the signal jumps away.
- **Harder to jam.** A jammer stuck on one frequency only hits the hops that land there. This is protection against **denial of service (DoS)**.

Classic **Bluetooth** hops **1,600 times a second** across **79 channels**. The idea is older than computers: actress Hedy Lamarr and composer George Antheil patented frequency hopping in 1942, to stop radio-guided torpedoes from being jammed.

**MF-TDMA** (multi-frequency TDMA) mixes chapter 3's time slots with hopping: each sender gets time slots, and those slots can sit on different carrier frequencies, so a sender may jump carriers from one slot to the next. Satellite networks use it.

## Side by side

| | DSSS | FHSS |
|---|---|---|
| How it spreads | Each bit becomes a chipping code | Hops between narrow channels |
| Channel use | One wide channel, all the time | One narrow channel at a time |
| Strength | Survives noise and narrow interference | Resists eavesdropping and jamming |
| Examples | Early Wi-Fi, Zigbee, CDMA cellular | Bluetooth, MF-TDMA satellite links |

Next, a check on spread spectrum.
