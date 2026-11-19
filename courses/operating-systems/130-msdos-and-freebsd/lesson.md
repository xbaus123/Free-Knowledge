# Process Control in Practice: MS-DOS and FreeBSD

*Chapter 2 · Part 4: Types of System Calls.*

Two systems, two very different ways to run a program.

## MS-DOS: one thing at a time

MS-DOS is **single-tasking**.

1. When the system boots, the **shell (command interpreter) is invoked**.
2. To run a program, it uses a **simple method: no process is created.** There's a **single memory space**.
3. The program is **loaded into memory, overwriting all but the kernel**, including most of the command interpreter.
4. When the **program exits, the shell is reloaded**.

```
  At system startup        Running a program
 +------------------+     +------------------+
 |                  |     |   free memory    |
 |   free memory    |     +------------------+
 |                  |     |                  |
 +------------------+     |     process      |
 |    command       |     |                  |
 |   interpreter    |     +------------------+
 +------------------+     | command interp.  |  (small leftover piece)
 |      kernel      |     |      kernel      |
 +------------------+     +------------------+
```

## FreeBSD: many at once

FreeBSD is a **UNIX variant** and **multitasking**.

1. When a user **logs in**, the system runs the **user's choice of shell**.
2. To run a program, the shell executes **`fork()`** to **create a new process**.
3. The new process executes **`exec()`** to **load the program into itself**.
4. The shell then either **waits for the process to terminate** or, if the command was run in the background, **continues with user commands** right away.

```
 +------------------+
 |    process D     |
 +------------------+
 |   free memory    |
 +------------------+
 |    process C     |
 +------------------+
 |   interpreter    |   (the shell stays in memory)
 +------------------+
 |    process B     |
 +------------------+
 |      kernel      |
 +------------------+
```

## Exit codes

When a FreeBSD process exits, it hands the shell an **exit code**:

| Code | Meaning |
|---|---|
| `0` | **No error** |
| `> 0` | **An error code** (which number says which error) |

Shell scripts check these codes to decide what to do next. In `bash`, `$?` holds the last command's code.

A check on the two systems.
