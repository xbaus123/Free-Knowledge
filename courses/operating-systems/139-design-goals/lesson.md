# Design Goals

*Chapter 2 · Part 6: Design and Implementation.*

How do you design an operating system? Honestly: **the design and implementation of an OS is not "solvable"**. There's no single right answer. But **some approaches have proven successful**, and **the internal structure of different operating systems can vary widely**.

## Start with goals

**Start the design by defining goals and specifications.** Two things shape them from the very top:

- **The choice of hardware.** An OS for a phone's ARM chip faces different limits than one for a server.
- **The type of system**: traditional desktop, mobile, distributed, real time, and so on.

## Two sets of goals

Goals split by who wants them:

| User goals | System goals |
|---|---|
| The OS should be **convenient to use** | It should be **easy to design, implement, and maintain** |
| **Easy to learn** | **Flexible** |
| **Reliable** | **Reliable** |
| **Safe** | **Error-free** |
| **Fast** | **Efficient** |

Users are the people *using* the system. The "system" side is the people who *build and maintain* it.

## The trouble with goals

Notice how **vague** these are. "Convenient" and "fast" don't tell an engineer what to write. And they **conflict**: making a system fast can make it harder to maintain; making it safe can make it less convenient. There's no general solution to these requirements. Each system strikes its own balance, which is a big reason operating systems differ so much inside.

Notice also that **reliable** appears on both sides. Users want a system that doesn't crash; builders want one that behaves predictably so it can be maintained.

A check on design goals.
