# Symmetric Multiprocessing and Multicore

*Chapter 1 · Part 3: Computer-System Architecture.*

Once a machine has several CPUs, who does what? There are two answers, and one of them won.

## Asymmetric multiprocessing

In **asymmetric multiprocessing**, **each processor is assigned a specific task**. One processor might handle I/O while another runs user code; each sticks to its own job.

## Symmetric multiprocessing (SMP)

In **symmetric multiprocessing** (SMP), **each processor performs all tasks**, including OS functions and user processes. 

```
  ┌──── CPU0 ────┐   ┌──── CPU1 ────┐   ┌──── CPU2 ────┐
  │  registers   │   │  registers   │   │  registers   │
  │    cache     │   │    cache     │   │    cache     │
  └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
         └──────────────────┼──────────────────┘
                         memory
```

Each CPU has **its own registers and its own cache**, but they all **share one memory**.

## Multi-chip and multicore

Multiple processors can be built as **multiple separate chips** (multi-chip), or as **multiple computing cores on a single chip**: **multicore**.

```
  ┌────────────── one chip ──────────────┐
  │  ┌── core0 ──┐        ┌── core1 ──┐  │
  │  │ registers │        │ registers │  │
  │  │   cache   │        │   cache   │  │
  │  └─────┬─────┘        └─────┬─────┘  │
  └────────┼────────────────────┼────────┘
           └─────── memory ─────┘
```

This is a **dual-core design**: two cores on one chip, each with its own registers and cache, sharing memory, just like the SMP picture above.

## Systems containing all chips

Going bigger still, some systems are a **chassis containing multiple separate systems**: several complete computers packed into one box.

Next, a check on SMP and multicore.
