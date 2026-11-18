# The Timer

*Chapter 1 · Part 4: Operating-System Structure and Operations.*

Dual mode stops a program from running privileged instructions. But it doesn't stop this:

```c
while (1) { }   /* never makes a system call, never causes a trap */
```

That loop uses only ordinary, harmless instructions. It never traps, never asks the OS for anything, and **never gives the CPU back**. On a single-CPU machine, the OS would never run again.

## The fix: a timer

The OS uses a hardware **timer** to **prevent an infinite loop or a process hogging resources**. The timer is set to **interrupt the computer after some time period**.

How it works:

1. The OS keeps a **counter** that is **decremented by the physical clock** (every tick, the counter goes down by one).
2. The OS **sets the counter** before giving the CPU to a program. Setting it is a **privileged instruction**, so the program can't turn the timer off or reset it.
3. When the counter reaches **zero**, the timer **generates an interrupt**.
4. The interrupt switches the CPU to kernel mode and runs the OS.

## Regaining control

The OS sets up the timer **before scheduling a process**, so it is **guaranteed to regain control**, however badly the process behaves. When the timer fires, the OS can:

- **Terminate a program that exceeded its allotted time**, or
- Let it continue later, and give the CPU to another process. That's exactly how timesharing switches between programs many times a second.

## Hardware protection, summed up

| Threat | Hardware defense |
|---|---|
| A program runs a dangerous instruction | **Dual mode**: privileged instructions trap in user mode |
| A program never gives up the CPU | **Timer**: an interrupt always comes |

Next, a check on the timer.
