# Timesharing

*Chapter 1 · Part 4: Operating-System Structure and Operations.*

Multiprogramming keeps the CPU busy, but in a batch system a user may wait hours for their job. You can't **interact** with it while it runs. **Timesharing** fixes that.

## Switching fast

**Timesharing** (or **multitasking**) is a **logical extension of multiprogramming**. The CPU still switches between jobs, but **so frequently that users can interact with each job while it's running**. That's **interactive computing**.

Each user gets a small slice of CPU time, many times a second. Every person at a terminal feels like they have the whole machine.

## What it takes

Making that illusion work needs several pieces, each a whole chapter later in this course:

| Need | Solution |
|---|---|
| Users expect quick replies | **Response time** should be **under 1 second** |
| Each user has at least one program running in memory | A program loaded and executing is a **process** |
| Several jobs are ready to run at the same time | The OS must choose: **CPU scheduling** |
| Not all the processes fit in memory | **Swapping** moves processes in and out of memory to run |
| A process is bigger than memory, or we want more of them | **Virtual memory** allows execution of a process **not completely in memory** |

## Multiprogramming vs timesharing

| | Multiprogramming | Timesharing |
|---|---|---|
| Goal | Keep the CPU busy | Keep users happy: fast interaction |
| When does the CPU switch? | When the running job has to wait | Also on a regular, short time slice |
| User experience | Submit a job, come back later | Type a command, see the result now |

Every OS you use today, on a laptop or phone, is a timesharing system. Dozens of processes share the CPU, switched many times a second.

Next, a check on timesharing.
