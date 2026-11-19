# Services for the User

*Chapter 2 · Part 1: Operating-System Services.*

Six services make the computer useful to you and your programs.

## 1. User interface

Almost every OS has a **user interface (UI)**. It comes in three styles: **command-line (CLI)**, **graphical (GUI)**, and **batch** (commands written into a file and run without anyone at the keyboard). Part 2 looks at each.

## 2. Program execution

The system must be able to **load a program into memory, run it, and end it**, either **normally** or **abnormally** (indicating an error).

## 3. I/O operations

A running program may need I/O, which might involve **a file or an I/O device**. Programs can't drive devices themselves (that's privileged, remember), so the OS does it for them.

## 4. File-system manipulation

The file system gets special attention. Programs need to **read and write** files and directories, **create and delete** them, **search** them, **list** file information, and manage **permissions**.

## 5. Communications

Processes often exchange information, either **on the same computer** or **between computers over a network**. There are two ways to do it:

- **Shared memory**: two processes read and write the same region of memory.
- **Message passing**: packets of information are **moved by the OS** from one process to another.

## 6. Error detection

The OS needs to be **constantly aware of possible errors**. They can happen:

- in the **CPU and memory hardware** (a memory error, a power failure),
- in **I/O devices** (a parity error on disk, a dropped network connection, a printer out of paper),
- in **user programs** (an arithmetic overflow, an illegal memory access).

For each type of error, the OS should **take the appropriate action** to keep computing correct and consistent. **Debugging facilities** help users and programmers use the system efficiently, and Part 8 comes back to them.

Next, a check on the six user services.
