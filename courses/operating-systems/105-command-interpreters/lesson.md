# The Command-Line Interface

*Chapter 2 · Part 2: User Interfaces.*

The oldest way to talk to an OS is to type at it. A **command-line interface (CLI)**, or **command interpreter**, lets you **enter commands directly**.

## What it does

Its main job is simple: **fetch a command from the user and execute it.** Read a line, figure out what it asks for, do it, and wait for the next line.

```
PBG-Mac-Pro:~ pbg$ pwd
/Users/pbg
PBG-Mac-Pro:~ pbg$ ls
Applications  Desktop  Documents  Downloads  Music ...
PBG-Mac-Pro:~ pbg$ ping 192.168.1.1
64 bytes from 192.168.1.1: icmp_seq=0 ttl=64 time=2.257 ms
```

## Where it lives

- Sometimes the command interpreter is **implemented in the kernel**.
- More often it's a **system program** that runs like any other program. That's how UNIX and Linux do it.

When there's more than one interpreter to choose from, each is called a **shell**. UNIX and Linux offer several: the Bourne shell (`sh`), the Bourne-Again shell (`bash`), the C shell (`csh`), the Z shell (`zsh`), and more. They do the same job with different features and syntax.

## Two ways to implement a command

| Approach | How `rm file.txt` works | Adding a new command |
|---|---|---|
| **Built-in** | The interpreter itself contains the code for `rm` and jumps to it | You must **change the shell** |
| **Program name** | The interpreter finds a program **file** named `rm`, loads it, and passes it `file.txt` | Just **drop a new program file in place**; the shell doesn't change |

UNIX mostly uses the second approach. The shell doesn't know what `rm` means at all. It just knows how to find a program by name and run it. That's why programmers can add new commands without touching the shell.

A few commands, like `cd`, *must* be built in. Changing the current directory changes the shell's own state, and a separate program can't do that for it.

A check, then the graphical side.
