# A Profiler in Python

*Chapter 2 · Part 8: Debugging, Generation, and Boot.*

Build the two tools from this part: a **sampling profiler**, and the **on-CPU time accounting** that the DTrace `sched.d` script does.

## Part 1: a sampling profiler

A profiler samples the **instruction pointer** at every timer tick. To turn addresses into something useful, it needs a **symbol table**: a list of `(start_address, function_name)` pairs, **sorted by start**. Each function runs from its start up to, but not including, the next function's start. The last function runs on forever.

1. **`function_at(symbols, address)`**: the function containing `address`, or `None` if it's below the first start. (`bisect.bisect_right` on the list of starts does this in one line, but a loop is fine too.)
2. **`profile(samples, symbols)`**: count samples per function: `{name: count}`. Samples in no function count as `"?"`.
3. **`hottest(samples, symbols, n)`**: the top `n` as `(name, percent)` pairs, most samples first. `percent` is `100 * count / len(samples)`, **rounded to one decimal place**. Break ties alphabetically by name.

```python
symbols = [(0x1000, "main"), (0x1400, "parse"), (0x2000, "draw")]
samples = [0x1004, 0x1500, 0x1510, 0x2100, 0x1520, 0x0500]
profile(samples, symbols)     # {"main": 1, "parse": 3, "draw": 1, "?": 1}
hottest(samples, symbols, 2)  # [("parse", 50.0), ("?", 16.7)]
```

Half the time is in `parse`: that's where to start tuning.

## Part 2: on-CPU time, DTrace style

4. **`cpu_time(events, uid=None)`**: `events` are `(timestamp, kind, program, user_id)` tuples in time order, where `kind` is `"on"` or `"off"` the CPU. Like `sched.d`:
   - On `"on"`, remember the timestamp for that program.
   - On `"off"`, add the time since its `"on"` to the program's total, and forget the saved time. An `"off"` with no saved `"on"` is ignored.
   - If `uid` is given, skip events from any other user, like the `uid == 101` predicate.
   - Return `{program: total}`. A program still on the CPU at the end hasn't been added yet.

```python
events = [(0, "on", "java", 101), (40, "off", "java", 101),
          (40, "on", "Xorg", 0),  (55, "off", "Xorg", 0),
          (55, "on", "java", 101), (60, "off", "java", 101)]
cpu_time(events)            # {"java": 45, "Xorg": 15}
cpu_time(events, uid=101)   # {"java": 45}
```

Use **Run** to try things out, and **Submit** to run the tests.
