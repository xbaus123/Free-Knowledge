# Processes and Threads

*Chapter 1 · Foundations.*

Before you spread work across many machines, you need to know what one machine does well and badly. Two facts shape almost every design in this course: **many things happen at once**, so shared data needs protection, and **storage is a hierarchy**, where each level down is bigger, cheaper, and dramatically slower.

## Processes and threads

A **process** is a running program with its own **address space**: its own view of memory, its own open files, its own crash. The operating system keeps processes apart, so one can't scribble over another's memory.

A **thread** is one sequence of execution *inside* a process. A process can run many threads, and they all share its memory.

| | Processes | Threads |
|---|---|---|
| Memory | Separate; talk through pipes, sockets, or files | Shared; any thread can read or write any variable |
| Cost to create and switch | Higher | Lower |
| A crash takes down | One process | Every thread in the process |
| Typical use | Isolation: one worker per request in older web servers, browser tabs | Concurrency within one service: a thread pool handling requests |

The **scheduler** decides which thread runs on each CPU core and switches between them (a **context switch**) many times a second. A switch can happen between *any* two instructions. Your code doesn't get a say.

Two words people mix up:

- **Concurrency**: several tasks in progress at once, interleaved. One core can do it by switching.
- **Parallelism**: several tasks *executing* at the same instant, on different cores.

Python's standard interpreter has a **global interpreter lock (GIL)** that lets only one thread run Python code at a time. That limits parallelism, but not concurrency: threads still interleave, so every bug in the next few readings happens in Python too.

Next, a short check on what you just read.
