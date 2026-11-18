# An Interrupt-Driven OS

*Chapter 1 · Part 4: Operating-System Structure and Operations.*

Part 2 said an operating system is **interrupt driven**. Now that several programs share the machine, that matters a lot more, because the OS has to stay in charge of all of them.

## Two kinds of interrupt

Modern operating systems are interrupt driven by both **hardware** and **software**:

- A **hardware interrupt** comes from one of the devices: the disk finished, a key was pressed, a packet arrived, the timer went off.
- A **software interrupt** is an **exception** or **trap**, caused by the running program.

## What causes a trap?

| Cause | Example |
|---|---|
| A **software error** | Division by zero; touching memory the program doesn't own |
| A **request for an operating-system service** | A **system call**: "open this file", "send these bytes", "create a process" |

When a trap occurs, the hardware transfers control to the OS, which decides what to do: run the requested service, or, for an error, usually **terminate the program** and report the problem.

## Problems the OS must guard against

With many programs sharing one machine, one bad program could hurt the others. The OS has to handle:

- An **infinite loop**: a program that never gives the CPU back.
- **Processes modifying each other**: one program scribbling over another's memory.
- **Processes modifying the operating system**: a program overwriting the kernel's code or data, or the interrupt vector.

A plain trap can catch some errors, like a divide by zero. But stopping a program from **doing harmful things it is allowed to try**, and **getting the CPU back** from a program that never stops, needs hardware help. The next two lessons cover it: **dual-mode operation** and the **timer**.

Next, a check on interrupts and traps in the running OS.
