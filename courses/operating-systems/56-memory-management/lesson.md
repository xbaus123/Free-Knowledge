# Memory Management

*Chapter 1 · Part 5: Resource Management.*

The CPU can only run instructions that are in **main memory**, and only work on data that's in memory. So memory is the stage every process has to stand on.

## The rule

- To execute a program, **all (or part) of its instructions must be in memory**.
- **All (or part) of the data** the program needs must be in memory.

"Or part" is the virtual-memory idea from Part 4: a process doesn't have to be entirely in memory to run.

## Why it needs managing

To keep the CPU busy and the system responsive, a computer keeps **several programs in memory at once** (multiprogramming). Somebody has to decide what goes where. **Memory management determines what is in memory and when**, with two goals:

- **Optimizing CPU utilization**: always have a ready process in memory.
- **Optimizing the computer's response to users**: the program you're using right now should be in memory, not on disk.

## What the OS does

The OS is responsible for these memory-management activities:

1. **Keeping track of which parts of memory are currently being used, and by whom.**
2. **Deciding which processes (or parts of them) and data to move into and out of memory.**
3. **Allocating and deallocating memory space as needed.**

```
  ┌──────────────┐  0
  │    kernel    │  ← owned by: OS
  ├──────────────┤
  │  process 12  │  ← owned by: alice's editor
  ├──────────────┤
  │     free     │  ← available to allocate
  ├──────────────┤
  │  process 40  │  ← owned by: bob's compiler
  ├──────────────┤
  │     free     │
  └──────────────┘
```

Next, a check on memory management.
