# Monolithic: Traditional UNIX

*Chapter 2 · Part 7: Operating-System Structure.*

UNIX went further than MS-DOS, but not all the way to clean layers.

**Limited by hardware functionality, the original UNIX had limited structuring.** It consists of **two separable parts**:

1. **System programs**
2. **The kernel**

## The kernel

The kernel **consists of everything below the system-call interface and above the physical hardware**. It provides **the file system, CPU scheduling, memory management, and other OS functions**: **a large number of functions for one level**.

```
                     (the users)
  -----------------------------------------------------
     shells and commands
     compilers and interpreters
     system libraries
  ========== system-call interface to the kernel ==========
  |  signals            file system          CPU scheduling    |
  |  terminal handling  swapping             page replacement  |  Kernel
  |  character I/O      block I/O system     demand paging     |
  |  terminal drivers   disk and tape drivers virtual memory   |
  ========== kernel interface to the hardware ============
     terminal controllers  device controllers  memory controllers
     terminals             disks and tapes     physical memory
```

The slides describe it as **beyond simple, but not fully layered**. There are clear boundaries at the top (the system-call interface) and the bottom (the hardware interface), but in between, everything is in **one big kernel**.

## Monolithic

That single-kernel design is called **monolithic**: one large program in **one address space**, running in kernel mode.

| Pro | Con |
|---|---|
| **Fast**: kernel parts call each other with plain function calls, with very little overhead | **Hard to implement and extend**: everything is tangled together |
| | A bug anywhere in the kernel can bring down everything |

The speed is why monolithic designs are still everywhere: **Linux, Windows, and macOS all have large monolithic parts**.

A check on UNIX's structure.
