# Real-Time Embedded Systems

*Chapter 1 · Part 7: Computing Environments.*

When you picture a computer you probably think of a laptop or phone. But the **most prevalent form of computer** is one you never see: the **real-time embedded system**.

## Embedded everywhere

Embedded computers run car engines and brakes, microwaves, washing machines, medical devices, robots, and factory equipment. They:

- **Vary considerably**: from tiny chips to complex controllers.
- Are **special purpose**, with a **limited-purpose OS**, often a **real-time OS**.
- Are **expanding in use** every year.

There are **many other special computing environments** as well. **Some have operating systems; some perform their tasks without an OS** at all.

## Real-time

A **real-time OS** has **well-defined, fixed time constraints**:

- **Processing must be done within the constraint.**
- The system has **correct operation only if the constraints are met**.

That's a different idea of "correct". In a desktop OS, a slow answer is annoying but still right. In a real-time system, **a right answer that comes too late is a wrong answer**. If a car's airbag controller detects a crash but fires the airbag a second late, it has failed, however good its calculation was.

| | General-purpose OS | Real-time OS |
|---|---|---|
| Goal | Good average performance, convenience | Meet every deadline |
| A late result is | Slow, but correct | **Incorrect** |
| Example | Laptop, phone | Airbag controller, pacemaker, factory robot |

Next, a check on real-time embedded systems.
