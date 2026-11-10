# How Signals Degrade: Attenuation, Bandwidth, and Noise

*Chapter 2 · Topologies and the Physical Layer.*

No medium is perfect. A signal gets weaker as it travels, picks up noise along the way, and can only carry so many bits per second. Five terms describe how well a medium copes.

## Segment length

The **segment length** is how far a signal can travel over a medium before it degrades to the point where it's **unintelligible**: the receiver can no longer tell a `1` from a `0`.

Every medium has a maximum segment length. Twisted-pair Ethernet is limited to **100 meters**. Fiber can run for kilometers. To go further, you put a **repeater** (or a switch) in the middle: it receives the weak signal, rebuilds it as a clean one, and sends it on.

## Attenuation

**Attenuation** is the measurable **loss of signal strength** as the signal travels. It's what sets the segment length. Attenuation is measured in **decibels (dB)**:

```
 loss (dB) = 10 × log10( power in / power out )
```

Decibels are logarithmic, so a few numbers are worth knowing by heart:

| Loss | Power left |
|---|---|
| 3 dB | about half |
| 10 dB | one tenth |
| 20 dB | one hundredth |
| 30 dB | one thousandth |

Losses add up: two 10 dB stretches of cable lose 20 dB, so a hundredth of the power gets through. Cable datasheets usually give attenuation **per 100 meters**, and longer cable means more loss.

## Bandwidth

**Bandwidth** is the **amount of data that can cross the medium in a given time**. It's measured in bits per second:

| Unit | Bits per second |
|---|---|
| kbps (kilobits) | 1,000 |
| Mbps (megabits) | 1,000,000 |
| Gbps (gigabits) | 1,000,000,000 |

Watch the capital letters: network speeds are in **bits** (small *b*), file sizes are usually in **bytes** (big *B*), and one byte is 8 bits. A 100 Mbps link moves at most 12.5 megabytes per second.

You'll also hear names like "5G", which isn't a unit at all. It's the fifth generation of cellular technology, which happens to offer a lot of bandwidth.

## Interference

**Interference** is the medium's **susceptibility to external noise** that can disrupt data transmission. The two kinds you'll hear about:

- **EMI (electromagnetic interference)**: noise from motors, fluorescent lights, power cables, elevators, and other electrical equipment.
- **RFI (radio-frequency interference)**: noise from radio transmitters, like nearby antennas, phones, and microwave ovens.

Copper cables act like antennas and pick both up. Fiber carries light, so it's immune to both.

## Crosstalk

**Crosstalk** happens when **signal conductors are placed too close to each other**: the signal on one wire leaks into its neighbor. On an old phone line, it's the faint other conversation you could hear in the background. In a network cable it shows up as bit errors.

## The five in one table

| Term | In one line | Unit or example |
|---|---|---|
| Segment length | How far before the signal is unintelligible | 100 m for twisted-pair Ethernet |
| Attenuation | Signal strength lost along the way | Decibels (dB) |
| Bandwidth | Data per unit of time | kbps, Mbps, Gbps |
| Interference | Outside noise getting in | EMI, RFI |
| Crosstalk | Neighboring wires leaking into each other | Wires bundled too close |

Next, a check on these five terms, including a little decibel arithmetic.
