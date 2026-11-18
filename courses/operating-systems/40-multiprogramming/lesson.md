# Multiprogramming

*Chapter 1 · Part 4: Operating-System Structure and Operations.*

Parts 2 and 3 were about hardware. Now the software: how does an OS keep that hardware busy?

## The problem: one program can't keep the CPU busy

A single user, running a single program, **cannot keep the CPU and the I/O devices busy at all times**. Programs constantly stop to wait: for a disk read, for a network reply, for the user to type. While one program waits, the CPU sits idle.

A program that computes for 1 ms, then waits 9 ms for the disk, keeps the CPU busy only **10%** of the time.

## The fix: keep several jobs in memory

**Multiprogramming** organizes **jobs** (code and data) so **the CPU always has one to execute**. Early systems that did this were called **batch systems**: users handed in jobs and came back later for the results.

1. The OS keeps a **subset of the total jobs in the system in memory** at once.
2. One job is selected and run via **job scheduling**.
3. When that job **has to wait** (for I/O, for example), the OS **switches to another job**.
4. When that one waits, it switches again. As long as at least one job is ready, the CPU is never idle.

A lawyer doesn't work for only one client at a time: while one case waits for a court date, they work on another. Same idea.

## Memory layout

```
 0     ┌──────────────────┐
       │ operating system │
       ├──────────────────┤
       │      job 1       │
       ├──────────────────┤
       │      job 2       │
       ├──────────────────┤
       │      job 3       │
       ├──────────────────┤
       │      job 4       │
 512M  └──────────────────┘
```

The OS sits in low memory, and several jobs share the rest.

Next, a check on multiprogramming.
