# I/O Structure

*Chapter 1 · Part 2: Computer-System Organization.*

A program asks to read a file. The disk is slow: thousands of times slower than the CPU. What does the program do while it waits? There are two designs.

## Synchronous I/O: wait for it

After I/O starts, **control returns to the user program only when the I/O completes**. The CPU has to do something in the meantime:

- A **wait instruction** idles the CPU until the next interrupt.
- Or a **wait loop** spins, checking over and over. (This also causes **contention for memory access**, since the loop keeps hitting the bus.)

The catch: **at most one I/O request is outstanding at a time**. No simultaneous I/O processing. Simple, but the CPU and every other device sit idle while one transfer finishes.

## Asynchronous I/O: carry on

After I/O starts, **control returns to the user program without waiting** for the I/O to complete. That needs some bookkeeping:

- A **system call** lets the user program ask the OS to wait for the I/O to complete, if and when it needs the result.
- A **device-status table** has an entry for **each I/O device**, giving its **type, address, and state** (idle, busy, not working).
- When an interrupt comes in, the OS **indexes into the device-status table** to find that device's entry, updates it to record the interrupt, and wakes whoever was waiting.

| Device | Type | Address | State | Waiting requests |
|---|---|---|---|---|
| disk 0 | disk | 0x1F0 | busy | read file A, then write file B |
| card reader 1 | input | 0x300 | idle | — |
| printer 3 | output | 0x378 | busy | print job 1234 |

Because each device has its own entry and its own queue of requests, **many I/O operations can be in progress at once**. Modern operating systems work this way.

Next, a check on I/O structure.
