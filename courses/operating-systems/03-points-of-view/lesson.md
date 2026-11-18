# Two Points of View

*Chapter 1 · Part 1: What Operating Systems Do.*

What an operating system should do **depends on who's looking**. The same OS looks different to someone using it than to the hardware it manages.

## The user's view

A user wants **ease of use** and **good performance**. They don't care about **resource utilization**: how well the CPU, memory, and disks are shared. Whether the CPU is busy 20% or 90% of the time doesn't matter to someone editing a document, as long as it feels fast.

But the "user" differs a lot from one machine to the next:

| Machine | What its OS optimizes for |
|---|---|
| **Personal laptop or desktop** | One user: convenience and speed for that person |
| **Mainframe or minicomputer** | Many users share one machine, so the OS must keep **all** of them happy: fair, efficient sharing |
| **Workstation** | Dedicated resources for one user, but frequently uses shared resources from **servers** (files, printers) |
| **Handheld (phone, tablet)** | Resource poor, so optimized for **usability and battery life** |
| **Embedded computer** | Little or no user interface at all: the computer in a car's brakes, a microwave, or a thermostat just runs |

## The system's view

From the computer's point of view, the OS is the program most intimately involved with the hardware. Two roles describe it:

**The OS is a resource allocator.** It manages all the resources: CPU time, memory space, storage space, and I/O devices. When requests conflict (two programs both want the printer, ten processes want the CPU), it decides who gets what, aiming for use that is both **efficient and fair**.

**The OS is a control program.** It controls the execution of user programs to **prevent errors and improper use** of the computer. A buggy program shouldn't be able to crash the machine or overwrite another program's memory.

A quick way to remember them: as allocator, the OS **shares** the machine; as control program, it **protects** the machine.

Next, a check on the user and system views.
