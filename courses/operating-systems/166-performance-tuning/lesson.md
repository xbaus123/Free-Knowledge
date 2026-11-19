# Performance Tuning

*Chapter 2 · Part 8: Debugging, Generation, and Boot.*

A system that works but is slow still has a problem. **Performance tuning** aims to **improve performance by removing bottlenecks**.

## Bottlenecks

A **bottleneck** is the one resource holding everything else back. If the CPU is idle while every process waits on the disk, a faster CPU won't help; the disk is the bottleneck. Tuning means finding it, fixing it, and then finding the next one.

## Measuring

You can't fix what you can't see, so **the OS must provide means of computing and displaying measures of system behavior**. Examples:

- **`top`** on UNIX and Linux: a live list of processes sorted by CPU use, with memory, load averages, and more.
- **Windows Task Manager**: CPU usage and history, memory use, number of processes, threads, and handles.

## Two ways to collect data

**Trace listings.** Record activities **as they happen** (every system call, every interrupt, every disk request) into a **trace** for analysis later. Very detailed; can be huge.

**Profiling.** **Periodic sampling of the instruction pointer** to look for **statistical trends**. Every few milliseconds, a timer interrupt fires and the OS notes *where the CPU was*: which address, and so which function. After thousands of samples, the functions that show up most are where the time goes.

| | Trace listing | Profiling |
|---|---|---|
| Records | Every event, as it happens | Samples at regular intervals |
| Detail | Exact | Statistical |
| Cost | High (records everything) | Low (one note per tick) |
| Good for | "What happened, in what order?" | "Where is the time going?" |

Profiling works because the timer interrupt (chapter 1) gives the OS control at regular moments anyway. Recording one address per tick costs almost nothing.

A check on performance tuning.
