# So What Exactly Is the OS?

*Chapter 1 · Part 1: What Operating Systems Do.*

Here's an awkward fact: there's **no universally accepted definition** of what's part of the operating system and what isn't.

## "Everything the vendor ships"

One rough approximation: the OS is **everything a vendor ships when you order an operating system**. That's useful, but it varies wildly. One vendor's OS is a few megabytes with a command line; another's includes a web browser, a photo app, and a music player.

## The kernel

A tighter definition: the OS is **the one program running at all times on the computer**. That program is called the **kernel**.

The kernel is loaded at startup and stays in memory until the machine shuts down. It's what actually manages the CPU, memory, and devices.

## Everything else

Everything that isn't the kernel is one of two things:

| Kind | What it is | Examples |
|---|---|---|
| **System program** | Ships with the OS but isn't part of the kernel | A file manager, the shell, `ls`, disk utilities, the login program |
| **Application program** | Everything not associated with running the system | A spreadsheet, a game, a web browser you downloaded |

## Putting it together

```
   applications            (spreadsheet, game, browser)
   system programs         (shell, file manager, utilities)
   ─────────────────────── the line where "user" code ends
   kernel                  (always running: CPU, memory, devices)
   hardware
```

When this course says "the OS does X", it usually means **the kernel** does X.

Next, a check on the kernel, system programs, and application programs.
