# System Calls and APIs

*Chapter 2 · Part 3: System Calls.*

Every service from Part 1 is reached the same way: through a **system call**.

## What a system call is

**System calls are the programming interface to the services provided by the OS.** They're how a user-mode program asks the kernel to do something it isn't allowed to do itself (from chapter 1: a system call traps into kernel mode, the kernel does the work, and control returns to user mode).

They're typically **written in a high-level language (C or C++)**, though the very lowest-level pieces may need assembly.

## You rarely call them directly

Programs mostly reach system calls through a high-level **Application Programming Interface (API)**: a set of functions, with their parameters and return values, that the programmer can use. The three most common:

| API | Used on |
|---|---|
| **Win32 API** | Windows |
| **POSIX API** | POSIX-based systems: virtually all versions of UNIX, Linux, and macOS |
| **Java API** | The Java virtual machine (JVM) |

Behind the scenes, an API function usually invokes one or more actual system calls. Why go through an API?

- **Portability**: a program written to POSIX compiles and runs on any POSIX system, even though the underlying system calls differ.
- **Ease**: actual system calls are often more detailed and harder to use than the API.

## How many system calls does a simple program make?

Plenty. Here's a program that **copies one file to another**:

```
Acquire input file name        (write prompt to screen, accept input)
Acquire output file name       (write prompt to screen, accept input)
Open the input file            (if it doesn't exist, abort)
Create the output file         (if it exists, abort)
Loop
    Read from input file
    Write to output file
Until read fails
Close output file
Write completion message to screen
Terminate normally
```

Nearly every line is a system call, and the loop makes two per block of data. Even simple programs lean heavily on the OS; a big copy makes **thousands** of system calls.

*One note: this course, like the textbook, uses **generic** system-call names. Real systems spell them differently, as you'll see in Part 4.*

A check, then a real API up close.
