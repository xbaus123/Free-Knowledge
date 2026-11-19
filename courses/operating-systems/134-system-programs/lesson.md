# System Programs

*Chapter 2 · Part 5: System Programs.*

Between the kernel and your apps sits a layer of **system programs** (also called **system utilities**). They **provide a convenient environment for program development and execution**.

Some are **simply user interfaces to system calls**: `rm` barely does more than call `unlink()`. Others are **considerably more complex**, like a compiler.

## The categories

| Category | What's in it |
|---|---|
| **File management** | **Create, delete, copy, rename, print, dump, list**, and generally manipulate files and directories |
| **Status information** | Ask the system for the **date, time, available memory, disk space, number of users**; or detailed **performance, logging, and debugging** information |
| **File modification** | **Text editors** to create and modify files; commands to **search** file contents or **transform** the text |
| **Programming-language support** | **Compilers, assemblers, debuggers, and interpreters** |
| **Program loading and execution** | **Absolute loaders, relocatable loaders, linkage editors, and overlay loaders**, plus debugging systems for high-level and machine language |
| **Communications** | Create **virtual connections among processes, users, and computers**: send messages to another user's screen, **browse the web, send email, log in remotely, transfer files** |
| **Background services** | Programs that run quietly all the time (next lesson) |

## Status information, a closer look

Status programs typically **format their output and print it to the terminal** or another output device: `date`, `df` (disk free), `who`, `top`.

Some systems also keep a **registry**: a database used to **store and retrieve configuration information**. Windows is the famous example.

## The user's view

Here's a key point: **most users' view of the operating system is defined by system programs, not by the actual system calls.** When you think of "macOS" you picture Finder, Terminal, and Settings, not `fork()` and `mmap()`. Two systems with very different kernels can feel alike if their system programs are alike, and the same kernel can feel completely different under different system programs.

A check on system programs.
