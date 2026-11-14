# Creating Resilient Data

*Chapter 10 · Resilience.*

How do you make **data itself** resilient: hard to tamper with, easy to check, and possible to rebuild? The four Rs again.

## Robustness

- **Show the same data in different states**: the same value kept in more than one form (a count and a running total, a value and its hash) so they can be checked against each other.
- **Tamper proof**, resisting distortion: hashes, signatures, append-only logs.
- **Explainable values**: you can say *why* a value is what it is. A total that matches its line items is explainable; a number that just appeared isn't.
- **Data bound to environment variables**: values tied to their context (time, location, state), so a value that doesn't fit its context stands out.

## Resourcefulness

- **Determine constant values**: what should **never** change? A server's serial number, a sensor's location.
- **Determine normal ranges** for values that **do** change, **for each meta-state**.

### The six meta-states

A system's "normal" depends on what it's doing. Six processing **meta-states**:

| Meta-state | What's going on | Example: CPU use |
|---|---|---|
| **Start-up** | Booting, loading | Spikes briefly |
| **Idle** | Running, nothing to do | 1 to 5% |
| **Normal** | Ordinary work | 20 to 50% |
| **Busy** | Peak load | 60 to 90% |
| **Failing** | Degrading: errors rising, slowing down | Erratic |
| **Failed** | Stopped doing its job | Zero, or stuck at 100% |

80% CPU is fine when **busy** and alarming when **idle**. Ranges per meta-state catch problems that one global range would miss.

### Temporal baselines

Time matters too. Keep separate baselines for:

- **Workdays** and **weekends**
- **Holidays**
- **Time of year** (a shop's December isn't its February)

Temporal baselines also **protect** the baselines themselves: an attacker who slowly raises traffic to make their activity look normal shows up against last year's same week.

## Redundancy

- **Baselines**: records of what normal looks like.
- **Saved values**: copies of key data from known-good times.

## Rapidity

- **Rebuild with partial information**: when some data is lost, use what's left.
- Keep the **key variables** and **baselined data**, and **recalculate lost values** from them.

RAID 5 is the classic example: lose a drive, and its contents are recalculated from the others and the parity. If you know a total and all but one of its parts, the missing part is the total minus the rest.

Next, a check.
