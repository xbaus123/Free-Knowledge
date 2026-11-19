# DTrace: Live Instrumentation

*Chapter 2 · Part 8: Debugging, Generation, and Boot.*

Tracing a production system is risky: you can't stop it, and you can't afford to slow it down much. **DTrace** was built for exactly that.

## What it is

**DTrace**, available in **Solaris, FreeBSD, and Mac OS X**, allows **live instrumentation on production systems**. You can ask questions of a running kernel and running apps, safely, without restarting anything.

## Probes, providers, and consumers

| Term | Meaning |
|---|---|
| **Probe** | A point in the code that can **fire when it's executed**, capturing state data |
| **Provider** | The part of DTrace that **owns a set of probes** in some area (for example, `sched` for the scheduler, `syscall` for system calls) |
| **Consumer** | A program that **receives the data** from the probes it has enabled |

So: **probes fire when code is executed within a provider, capturing state data and sending it to the consumers of those probes.**

## Following a system call

One example from the slides follows the `XEventsQueued` call. It starts in user mode in the library (`U`), crosses into the kernel (`K`) through `ioctl`, runs a chain of kernel functions, then climbs back out to user mode:

```
CPU FUNCTION
  0 -> XEventsQueued               U
  0   -> _XEventsQueued            U
  0     -> ioctl                   U
  0       -> ioctl                 K
  0         -> getf                K
  0         <- getf                K
  ...
  0       <- ioctl                 K
  0     <- ioctl                   U
  0 <- XEventsQueued               U
```

`->` is entering a function, `<-` is returning. You can watch a call go from the library into the kernel and back, the path you studied in Part 3.

## Measuring CPU time

A tiny DTrace script can record **how long each process belonging to user 101 spends running on the CPU**, in nanoseconds:

```
sched:::on-cpu
uid == 101
{
    self->ts = timestamp;
}

sched:::off-cpu
self->ts
{
    @time[execname] = sum(timestamp - self->ts);
    self->ts = 0;
}
```

When a process **goes on the CPU**, note the time. When it **goes off**, add the elapsed time to that program's total. The output lists programs like `gnome-terminal` and `java` with their total on-CPU nanoseconds. You'll build the same calculation in Python next.

A check on DTrace.
