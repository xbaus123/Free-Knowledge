# Hybrid Systems

*Chapter 2 · Part 7: Operating-System Structure.*

Here's the truth about real systems: **most modern operating systems are not one pure model**.

A **hybrid** combines multiple approaches to address **performance, security, and usability** needs.

| System | What it combines |
|---|---|
| **Linux** and **Solaris** | Kernel in **kernel address space**, so **monolithic** (for speed), **plus modular** for dynamic loading of functionality |
| **Windows** | **Mostly monolithic**, **plus microkernel** ideas for different **subsystem personalities** (environments that let it run programs written for other APIs) |
| **macOS** | **Hybrid and layered** (next section) |

## macOS

macOS is layered on the outside and hybrid at its core:

```
  +-------------------------------------------------------+
  | graphical user interface:            Aqua             |
  +-------------------------------------------------------+
  | application environments and services:                |
  |     ( Java )   ( Cocoa )   ( Quicktime )   ( BSD )    |
  +-------------------------------------------------------+
  | kernel environment:                                   |
  |                   +-----------------------------------+
  |      Mach         |              BSD                  |
  |                   +-----------------------------------+
  +---------------------------+---------------------------+
  |          I/O kit          |     kernel extensions     |
  +---------------------------+---------------------------+
```

- **Aqua** is the GUI.
- **Cocoa** is the **programming environment** (an API for writing Mac apps, in Objective-C or Swift).
- Below them is the **kernel**, which combines:
  - the **Mach microkernel**: memory management, IPC, thread scheduling,
  - **BSD UNIX parts**: the POSIX API, networking, file systems, the command line,
  - the **I/O kit** for writing device drivers,
  - and **dynamically loadable modules, called kernel extensions**.

Although Mach is a microkernel, in macOS Mach and BSD run **in the same kernel address space**, so they talk by function call, not message passing. That's the hybrid: microkernel design, monolithic speed, loadable extensions.

A check on hybrids.
