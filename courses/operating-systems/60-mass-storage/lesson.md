# Mass-Storage Management

*Chapter 1 · Part 5: Resource Management.*

Main memory is too small to hold everything, and it forgets at power off. So **disks** (HDDs and SSDs) store data that **doesn't fit in main memory**, or that must be kept for a **"long" period of time**.

## Why it matters

Programs, from compilers to web browsers, are stored on disk until they're loaded, and many use disk as both source and destination of their work. So **proper management is of central importance**: the **entire speed of computer operation can hinge on the disk subsystem and its algorithms**.

## What the OS does

1. **Free-space management**: tracking which blocks are unused.
2. **Storage allocation**: choosing which free blocks a new or growing file gets.
3. **Disk scheduling**: when many requests are waiting, choosing the **order to serve them in**. On a hard disk, serving requests in a smart order can avoid moving the heads back and forth, cutting wait times a lot.

## Tertiary storage

**Some storage need not be fast.** **Tertiary storage** is the level below disks:

- **Optical storage** (CDs, DVDs, Blu-ray)
- **Magnetic tape**

It's used for backups, archives, and rarely used data. Tertiary storage **still must be managed**, either **by the OS or by applications** (a backup program, for example).

Media range from **WORM** (write-once, read-many-times, like a CD-R: you burn it once) to **RW** (read-write: rewritable as often as you like).

| Level | Examples | Speed | Typical use |
|---|---|---|---|
| Primary | Registers, cache, main memory | Fastest | Running programs |
| Secondary | SSD, hard disk | Medium | Files and programs |
| Tertiary | Optical disks, tape | Slowest | Backups, archives |

Next, a check on mass storage.
