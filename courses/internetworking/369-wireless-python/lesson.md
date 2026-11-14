# A Wireless Toolkit in Python

*Chapter 11 · Wireless and IoT.*

Time to build the chapter's ideas. Each function uses an example from the readings or drills, so you can check your answers against them.

## Part 1: 2.4 GHz channels

- `center_mhz(channel)`: channels 1 to 13 sit at `2407 + 5 * channel` MHz, so channel 6 is `2437`. Channel 14 is the odd one, at `2484`. Raise `ValueError` for anything else.
- `overlaps(a, b)`: each signal is about 22 MHz wide, so two channels overlap when their centers are **less than 22 MHz apart**. `overlaps(1, 6)` is `False`, `overlaps(1, 3)` is `True`.
- `best_channel(neighbors)`: `neighbors` lists the channels nearby WAPs use. Of **1, 6, and 11**, return the one that overlaps the fewest of them. `best_channel([1, 1, 6])` is `11`. Ties go to the first of 1, 6, 11.

## Part 2: path loss

Radio weakens with distance even in empty space. The **free-space path loss**, in dB, is:

```
 fspl_db = 20 × log10(distance_m) + 20 × log10(freq_mhz) - 27.55
```

- `fspl_db(distance_m, freq_mhz)`: `fspl_db(10, 2437)` is about `60.19`. The same 10 m at 5 GHz loses more, which is why 2.4 GHz reaches farther. Raise `ValueError` unless both are positive.
- `received_dbm(tx_dbm, distance_m, freq_mhz, walls=())`: the transmit power minus the path loss, minus each wall's loss from `WALL_LOSS_DB` (the interference reading's table). `received_dbm(20, 10, 2437, ["drywall", "concrete"])` is about `-55.19`. Raise `ValueError` for a material that isn't in the table.

## Part 3: DSSS

- `spread(bits)`: every `1` becomes the 11-chip `BARKER` code and every `0` becomes it inverted, all in one list. Raise `ValueError` for anything but 0 or 1.
- `despread(chips)`: take the chips 11 at a time. If **more than half** of a group match `BARKER`, it's a `1`, otherwise a `0`. That majority vote is why noise doesn't hurt: up to 5 flipped chips per bit still decode. Raise `ValueError` if the chip count isn't a multiple of 11.

## Part 4: frequency hopping

Both ends of an FHSS link hop together because they run the same generator from the same seed.

- `hop_sequence(seed, hops, channels=79)`: start with `x = seed`. For each hop, step `x = (1103515245 * x + 12345) % 2**31`, then hop to channel `x % channels`. `hop_sequence(42, 5)` is `[50, 32, 27, 71, 57]`. Raise `ValueError` if `hops` is negative or `channels` is less than 1.
- `jammed_fraction(sequence, jammed)`: the fraction of hops that land on a jammed channel. `jammed_fraction([3, 7, 3, 9], [3])` is `0.5`. Raise `ValueError` for an empty sequence. Try a long sequence with one jammed channel to see why hopping resists jamming.

## Part 5: usage

- `usage_tier(mbps)`: `"light"` up to 25 Mbps, `"medium"` up to 300, and `"heavy"` above that, from the planning reading. Raise `ValueError` for negative bandwidth.

Use **Run** to try things out, and **Submit** to run the tests.
