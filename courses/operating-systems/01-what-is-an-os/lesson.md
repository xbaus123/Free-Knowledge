# What Is an Operating System?

*Chapter 1 · Part 1: What Operating Systems Do.*

Every program you've ever run, from a web browser to a "Hello, world", leaned on a piece of software you probably never think about: the **operating system** (OS). This course opens it up.

## The one-sentence definition

An operating system is **a program that acts as an intermediary between the user of a computer and the computer hardware.**

Your program says "open this file" or "draw this window". It doesn't know which disk the file is on, which sector holds it, or how to talk to that brand of graphics card. The OS does.

## Three goals

An operating system tries to:

1. **Execute user programs** and make solving the user's problems easier.
2. Make the computer system **convenient** to use.
3. Use the computer hardware **efficiently**.

The goals pull against each other. A phone OS leans hard on convenience; a server OS running a busy database leans on efficiency. Much of this course is about how real systems balance them.

## Four components of a computer system

You can split any computer system into four layers:

| Component | What it is | Examples |
|---|---|---|
| **Hardware** | Provides the basic computing resources | CPU, memory, I/O devices |
| **Operating system** | Controls and coordinates the hardware among the programs and users | Linux, Windows, macOS, Android |
| **Application programs** | Use the resources to solve the users' problems | Word processors, compilers, web browsers, databases, games |
| **Users** | Whoever wants work done | People, machines, other computers |

```
  user 1   user 2   user 3  ...  user n
     |        |        |           |
 [ compiler  assembler  text editor ... database ]   system and application programs
          [        operating system        ]
                [ computer hardware ]
```

Notice the shape: the OS sits **between** the programs and the hardware. Applications don't touch the hardware directly; they ask the OS.

Next, a short check on what an OS is and the four components.
