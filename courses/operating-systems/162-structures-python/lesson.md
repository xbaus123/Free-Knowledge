# OS Structures in Python

*Chapter 2 · Part 7: Operating-System Structure.*

Two of the structure trade-offs, measured: the **difficulty of defining layers**, and the **cost of microkernel messages**.

## Part 1: checking a layered design

**`layer_violations(levels, calls)`**. `levels` maps each module to its layer number (`0` is the hardware). `calls` is a list of `(caller, callee)` pairs. The layering rule says a module may only use modules in **lower** layers, so a call to the **same or a higher** layer is a violation. Return the violating calls, in their original order.

```python
layer_violations({"hw": 0, "mem": 1, "fs": 2}, [("fs", "mem"), ("mem", "fs")])
# [("mem", "fs")]
```

## Part 2: finding a layering

**`assign_layers(uses)`**. `uses` maps each module to the list of modules it uses. Give every module the **lowest layer it can have**:

- `0` if it uses nothing (a module that only appears inside lists uses nothing),
- otherwise `1 +` the highest layer among the modules it uses.

Return a dict covering every module mentioned anywhere.

Here's the hard part of layering: if modules use each other in a **cycle** (memory management needs the disk driver for swapping, and the disk driver needs memory management for buffers), **no layering exists**. Raise `ValueError`. A module using itself counts as a cycle.

```python
assign_layers({"fs": ["mem", "driver"], "driver": ["hw"], "mem": ["hw"]})
# {"fs": 2, "mem": 1, "driver": 1, "hw": 0}
```

*Hint:* a recursive helper that remembers finished modules, plus a set of modules "in progress", will spot cycles: reaching a module that's still in progress means you've gone round a loop.

## Part 3: counting the microkernel's cost

**`mode_switches(path, modes)`**. A request visits components in order, like `["app", "fs", "driver", "fs", "app"]`. `modes` says whether each runs in `"user"` or `"kernel"` mode. Add up each hop:

| Hop | Mode switches | Why |
|---|---|---|
| kernel → kernel | 0 | A plain function call inside the kernel |
| user → kernel, or kernel → user | 1 | A system call, or the return to user mode |
| user → user | 2 | A message: into the kernel, then out to the receiver |

Then compare:

```python
request = ["app", "fs", "driver", "fs", "app"]
mode_switches(request, {"app": "user", "fs": "kernel", "driver": "kernel"})  # 2  (monolithic)
mode_switches(request, {"app": "user", "fs": "user",   "driver": "user"})    # 8  (microkernel)
```

Four times the switches for the same file read. That's the microkernel's detriment, in one number.

Use **Run** to try things out, and **Submit** to run the tests.
