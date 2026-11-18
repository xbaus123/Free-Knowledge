# One CPU or Many?

*Chapter 1 · Part 3: Computer-System Architecture.*

Part 2 drew "one or more CPUs" on the bus. This part is about the "or more": how computers are built from one processor, several, or several whole machines.

## Single-processor systems

For a long time, most systems used a **single general-purpose processor**: one CPU that runs the OS and user programs.

Even those machines have **special-purpose processors** too: a disk controller's microprocessor, a keyboard's controller, a graphics processor. These run a limited set of instructions, don't run user programs, and are managed by the OS (it tells them what to do and checks their status). Having them doesn't make a system a "multiprocessor".

## Multiprocessor systems

**Multiprocessor** systems have **two or more processors** in close communication, sharing the computer bus and often the clock, memory, and devices. They're also known as **parallel systems** or **tightly-coupled systems**. Nearly every phone, laptop, and server is one today.

## Three advantages

1. **Increased throughput.** More processors get more work done in less time. But **N processors don't give an N× speedup**: there's overhead keeping the parts working together, and competition for shared resources like memory. Five people writing a report aren't five times faster than one.
2. **Economy of scale.** Multiprocessor systems can cost less than the same number of single-processor machines, because they **share** peripherals, storage, and power supplies. Storing data once on a shared disk beats copying it to ten separate computers.
3. **Increased reliability.** If work is spread across processors, the failure of one **doesn't halt the system**; it just slows it down.
   - **Graceful degradation**: continuing to provide service in proportion to the surviving hardware. Lose 1 of 10 CPUs, keep ~90% of the speed.
   - **Fault tolerance**: going further, surviving any single component failure and **continuing to operate as if nothing happened**. That needs duplicated hardware and a way to detect, diagnose, and correct the failure.

Next, a check on multiprocessors.
