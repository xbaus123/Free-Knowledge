# System Boot

*Chapter 2 · Part 8: Debugging, Generation, and Boot.*

Chapter 1 introduced the bootstrap program. Here's the full sequence.

## Step by step

1. **When power is initialized, execution starts at a fixed memory location.** The CPU is built to begin there; no software chose it.
2. That location is in **firmware ROM**, which **holds the initial boot code**. It's non-volatile, so it's there every time, and it can't be infected by a virus as easily as a disk can.
3. **The OS must be made available to the hardware so the hardware can start it.** A small piece of code, the **bootstrap loader**, stored in **ROM or EEPROM**, **locates the kernel, loads it into memory, and starts it**.
4. Sometimes it's a **two-step process**: the ROM code loads a **boot block** from a **fixed location** on disk, and the boot block's code **loads the bootstrap loader from disk**, which then loads the kernel.
5. The **kernel loads, and the system is then running**.

```
  power on
     |
     v
  firmware ROM at a fixed address     (initial boot code)
     |
     v
  boot block, at a fixed place on disk   (sometimes; the two-step process)
     |
     v
  bootstrap loader, e.g. GRUB         (finds and loads the kernel)
     |
     v
  kernel in memory                    (initializes, starts daemons)
     |
     v
  system running
```

## Why two steps?

ROM is small and hard to change. Keeping just a tiny loader in ROM, and the real bootstrap loader on disk, means you can **update the bootstrap loader** (or install a new OS) without replacing firmware.

**EEPROM** (electrically erasable programmable ROM) is the middle ground: non-volatile like ROM, but it **can be rewritten**, which is how firmware updates are installed.

## GRUB

**GRUB** is a common bootstrap loader on Linux systems. It **allows selection of a kernel from multiple disks, versions, and kernel options**. That's how a machine can **dual-boot** Linux and Windows, or let you fall back to last week's kernel if a new one won't start.

A check on booting.
