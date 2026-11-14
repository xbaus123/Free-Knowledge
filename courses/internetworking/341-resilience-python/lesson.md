# A Resilience Toolkit in Python

*Chapter 10 · Resilience.*

Time to put numbers on resilience. Every function uses an example from the readings or drills, so you can check your answers against them.

## Part 1: availability

- `availability(mtbf, mttr)`: `mtbf / (mtbf + mttr)`, from the reliability reading. `availability(99, 1)` is `0.99`. Raise `ValueError` if `mtbf` isn't positive or `mttr` is negative.
- `downtime_minutes(avail, days=365)`: the minutes of downtime that availability allows over that many days. `downtime_minutes(0.999)` is about `525.6`. Raise `ValueError` unless `avail` is between 0 and 1.

## Part 2: series and parallel

- `series(avails)`: every part must work, so multiply. `series([0.99, 0.99])` is `0.9801`.
- `parallel(avails)`: any one part is enough, so it fails only if all of them fail. `parallel([0.99, 0.99])` is `0.9999`.

Both raise `ValueError` for an empty list.

## Part 3: RAID

From the table in the hardware reading, for levels **0, 1, 5, and 6**:

- `raid_usable(level, drives, size)`: usable space. `raid_usable(5, 4, 2)` is `6`.
- `raid_tolerates(level, drives)`: how many drives can fail without losing data. `raid_tolerates(1, 3)` is `2`.

Raise `ValueError` for any other level, or too few drives for the level (2 for RAID 0 and 1, 3 for RAID 5, 4 for RAID 6).

## Part 4: rebuilding with parity

RAID 5 rebuilds a lost drive from the others with **XOR**. Blocks are `bytes` of equal length.

- `parity(blocks)`: XOR all the blocks together, byte by byte. Raise `ValueError` for no blocks, or blocks of different lengths.
- `rebuild(blocks, parity_block)`: exactly one of `blocks` is `None` (the lost drive). Return it. XOR of the parity and every surviving block gives it back. Raise `ValueError` unless exactly one block is missing.

## Part 5: baselines

`check_reading(value, state, baselines)` compares a reading to its meta-state's range. `baselines` maps a meta-state to `(low, high)`, inclusive. Return `"low"`, `"ok"`, or `"high"`. Raise `ValueError` if `state` isn't one of the six `META_STATES`, or has no baseline. These are the drill's examples:

```python
cpu = {"idle": (1, 5), "normal": (20, 50), "busy": (60, 90)}
check_reading(70, "idle", cpu)   # 'high'
check_reading(40, "busy", cpu)   # 'low'
```

Use **Run** to try things out, and **Submit** to run the tests.
