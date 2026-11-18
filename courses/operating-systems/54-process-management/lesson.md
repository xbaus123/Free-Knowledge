# Process Management

*Chapter 1 · Part 5: Resource Management.*

Part 1 said the OS is a **resource allocator**. This part is the tour of what it allocates, starting with the most important thing it manages: running programs.

## Program vs process

A **process** is **a program in execution**. It's the unit of work within the system.

- A **program** is a **passive entity**: a file of instructions sitting on disk.
- A **process** is an **active entity**: those instructions running, with a current position, values in registers, and memory in use.

Run the same program twice (two browser windows, two terminals) and you get **two processes** from one program.

## What a process needs

A process needs **resources** to do its task:

- **CPU** time, **memory**, **I/O** devices, and **files**.
- **Initialization data**: input to start with. A process that displays a file needs the file's name.

When a process **terminates**, the OS must **reclaim any reusable resources** it held: free its memory, close its files, release its devices.

## Threads and the program counter

- A **single-threaded** process has **one program counter** specifying the location of the **next instruction to execute**. It executes instructions **sequentially, one at a time**, until it completes.
- A **multi-threaded** process has **one program counter per thread**. Each thread is a separate path through the code, running concurrently: a browser can download a page in one thread while you scroll in another.

## Many processes at once

A typical system has **many processes**: some **user** processes, some **operating-system** processes (running system code), all running **concurrently** on one or more CPUs.

With fewer CPUs than processes, concurrency is achieved by **multiplexing the CPUs** among the processes or threads: each gets a turn, switched quickly by the scheduler and the timer.

## The OS's process-management jobs

The OS is responsible for:

1. **Creating and deleting** both user and system processes
2. **Suspending and resuming** processes
3. Providing mechanisms for **process synchronization** (so processes sharing data don't corrupt it)
4. Providing mechanisms for **process communication** (so processes can pass information)
5. Providing mechanisms for **deadlock handling** (so processes waiting on each other don't get stuck forever)

Each of these gets its own chapter later in the course.

Next, a check on process management.
