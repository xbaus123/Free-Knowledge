# Interrupts

*Chapter 1 · Part 2: Computer-System Organization.*

The disk controller has finished reading your file. How does the CPU find out? It could keep asking ("done yet? done yet?"), but that wastes time. Instead, the controller **interrupts** it.

## What an interrupt does

An **interrupt** is a signal to the CPU that something needs attention. When one arrives:

1. The CPU **stops** what it's doing.
2. It **transfers control** to a fixed location: the start of the **interrupt service routine** (ISR) for that kind of interrupt.
3. The ISR handles the event.
4. The CPU **resumes** the interrupted computation as if nothing had happened.

## The interrupt vector

How does the CPU know where the right ISR is? Generally, through the **interrupt vector**: a table that holds **the addresses of all the service routines**. Each kind of interrupt has a number, and that number picks the entry in the table.

| Interrupt number | Service routine address |
|---|---|
| 0 | address of routine 0 |
| 1 | address of routine 1 |
| ... | ... |
| 33 | address of routine 33 |

There's no searching: interrupt 33 goes straight to entry 33.

## Saving where you were

To resume afterward, the interrupt architecture must **save the address of the interrupted instruction**. Without it, the CPU wouldn't know where to go back to.

## Traps and exceptions

Not every interrupt comes from a device. A **trap** (or **exception**) is a **software-generated interrupt**, caused by either:

- **An error**: dividing by zero, or touching memory the program doesn't own.
- **A user request**: a program asking the OS for a service (a **system call**).

## The OS is interrupt driven

Put it together and you get the key idea: **an operating system is interrupt driven**. If no programs are running, no devices need service, and no users are typing, the OS just sits idle, waiting. Everything it does is a response to an interrupt or a trap.

Next, a check on interrupts.
