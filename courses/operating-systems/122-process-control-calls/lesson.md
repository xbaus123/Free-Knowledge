# Process-Control System Calls

*Chapter 2 · Part 4: Types of System Calls.*

There are hundreds of system calls, but they fall into **six categories**:

1. **Process control**
2. **File management**
3. **Device management**
4. **Information maintenance**
5. **Communications**
6. **Protection**

This lesson takes the first and biggest one.

## Process control

A running program needs to be able to start, stop, and manage programs, including itself:

| Calls | What they're for |
|---|---|
| **create process, terminate process** | Start a new program running; kill one |
| **end, abort** | Halt normally (end) or abnormally (abort) |
| **load, execute** | Load another program into memory and run it |
| **get / set process attributes** | Read or change a process's priority, maximum run time, and so on |
| **wait for time** | Pause for a set amount of time |
| **wait event, signal event** | Wait until something happens; announce that it has |
| **allocate and free memory** | Ask for memory and give it back |

Three more that are easy to forget:

- **Dump memory if error.** When a program aborts, the OS can write its memory to disk so a programmer can examine it later.
- **Debugger** support, for determining **bugs** and **single-step** execution: run one instruction, stop, let the programmer look around, repeat.
- **Locks** for managing access to **shared data between processes**: one process takes the lock, uses the data, then releases it, so two processes never change the data at once.

## End versus abort

A program that ends **normally** tells the OS it succeeded. One that **aborts** (or is killed for an error) ends abnormally, and the OS may dump memory and print an error message. Either way, control goes back to the command interpreter, which reads the next command.

A check on process-control calls.
