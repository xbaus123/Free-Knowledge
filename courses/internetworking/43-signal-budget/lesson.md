# Signal Budget: The Physical Layer in Python

*Chapter 2 · Topologies and the Physical Layer.*

Choosing a medium comes down to arithmetic: how much signal is lost over the run, how far you can go before it's too weak, how many repeaters a long run needs, and which cable is the cheapest one that does the job. Network engineers call this a **signal budget** (or *link budget*). You'll write the calculator.

## The formulas

Loss in decibels, from the power sent and the power received:

```
 loss_db = 10 × log10( power_in / power_out )
```

And back the other way, from a loss in decibels to the power that's left:

```
 power_out = power_in / 10 ** (loss_db / 10)
```

Python's `math.log10` does the logarithm. Check yourself with the numbers from the reading: half the power is about 3 dB, a tenth is 10 dB, a hundredth is 20 dB.

## Your task

Implement these six functions in the editor:

- `db_loss(power_in, power_out)`: the loss in dB. Raise `ValueError` if either power is zero or negative (the logarithm doesn't exist there).
- `power_after(power_in, db_per_100m, length_m)`: the power left after `length_m` meters of cable that loses `db_per_100m` decibels every 100 meters. Losses add up, so 250 m of 4 dB/100 m cable loses 10 dB.
- `max_segment(power_in, min_power, db_per_100m)`: the longest cable, in meters, that still delivers at least `min_power`. That's the **segment length** from the reading. Return `0.0` if `min_power` is already at or above `power_in`, and raise `ValueError` if `db_per_100m` is zero or negative.
- `repeaters_needed(distance_m, segment_m)`: how many repeaters it takes to cover `distance_m` when no segment can be longer than `segment_m`. A 250 m run with 100 m segments is three segments, so it needs **2** repeaters between them. Raise `ValueError` if `segment_m` is zero or negative.
- `transfer_seconds(size_bytes, mbps)`: how long it takes to send a file of `size_bytes` **bytes** over a link of `mbps` **megabits** per second. Remember: 8 bits to a byte, and 1 Mbps is 1,000,000 bits per second.
- `choose_medium(media, distance_m, min_mbps, noisy)`: pick a cable. `media` is a list of dictionaries like the `MEDIA` catalog at the top of the starter file. A medium qualifies if:
  - its `max_segment_m` is at least `distance_m` (one segment, no repeaters),
  - its `mbps` is at least `min_mbps`, and
  - when `noisy` is `True`, it's `emi_resistant`.

  Return the `name` of the qualifying medium with the lowest total cost (`cost_per_m × distance_m`). On a tie, the one listed first wins. If nothing qualifies, return `None`.

Use **Run** to try things out, and **Submit** to run the tests.
