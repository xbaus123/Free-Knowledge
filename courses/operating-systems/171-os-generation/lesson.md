# Operating-System Generation

*Chapter 2 · Part 8: Debugging, Generation, and Boot.*

Operating systems are **designed to run on any of a class of machines**: every PC with an x86 CPU, say, with any amount of memory and any mix of disks and devices. But each actual computer is specific. So **the system must be configured for each specific computer site**.

## SYSGEN

The **SYSGEN** (system generation) program **obtains information concerning the specific configuration of the hardware system**:

- What **CPU** is it? Which optional features (like floating-point instructions) does it have?
- **How much memory** is there?
- **Which devices** are attached, and what are their addresses and interrupt numbers?
- **OS options**: how many buffers? which CPU-scheduling algorithm? how many processes at most?

The information can come from the system administrator, or the program can **probe the hardware** to find out for itself.

## What it's used for

The answers are used in one of two ways:

1. **Build a system-specific compiled kernel**: compile the OS source with exactly the right settings and drivers.
2. **Tune a general kernel**: keep one kernel, but select modules and settings from tables at boot time.

A system-specific kernel **can generate more efficient code than one general kernel**: no drivers for hardware that isn't there, no checks for features that are missing, tables sized just right.

| | Custom-compiled kernel | General kernel, configured |
|---|---|---|
| Efficiency | **Higher** | Lower |
| Size | Smaller | Larger |
| Changing hardware | Rebuild the kernel | Just change settings or load a module |

Most modern desktop systems lean toward the general kernel plus **loadable modules** from Part 7: one kernel that detects its hardware at boot and loads the drivers it needs. Embedded systems, where every byte counts, often still build a custom kernel.

A check on system generation.
