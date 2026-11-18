# The I/O Subsystem

*Chapter 1 · Part 5: Resource Management.*

There are thousands of kinds of devices: keyboards, disks, cameras, game controllers, printers. **One purpose of the OS is to hide the peculiarities of hardware devices from the user.**

## What the I/O subsystem does

The **I/O subsystem** is the part of the kernel responsible for:

**1. Memory management of I/O**, which includes three techniques:

| Technique | What it does | Example |
|---|---|---|
| **Buffering** | Storing data **temporarily while it's being transferred** | A video player loads a few seconds ahead, so a network hiccup doesn't stop playback |
| **Caching** | Storing parts of data in **faster storage for performance** | Recently read file blocks kept in memory |
| **Spooling** | **Overlapping the output of one job with the input of other jobs** | Print jobs queue on disk while the printer works through them one at a time |

Spooling is why you can hit Print on three documents and go back to work immediately. Each job is written to a queue (the *spool*) on disk, and the printer takes them one at a time. A printer can only print one job at a time, but spooling lets many programs "use" it at once.

**2. A general device-driver interface**: a standard set of functions (open, read, write, close) that every driver provides, so the rest of the kernel treats all devices alike.

**3. Drivers for specific hardware devices**: the code that knows the quirks of one particular device controller. **Only the device driver knows the peculiarities of the specific device it's assigned to.**

```
   applications
   ─────────────── system calls
   kernel I/O subsystem   (buffering, caching, spooling)
   general device-driver interface
   [ disk driver ] [ USB driver ] [ GPU driver ] [ network driver ]
   ─────────────── hardware
   device controllers and devices
```

Next, a check on the I/O subsystem.
