# Policy and Mechanism

*Chapter 2 · Part 6: Design and Implementation.*

One design principle matters more than almost any other: **separate policy from mechanism**.

| | Question it answers |
|---|---|
| **Policy** | **What** will be done? |
| **Mechanism** | **How** to do it? |

**Mechanisms determine how to do something; policies decide what will be done.**

## The timer example

Chapter 1's **timer** is a mechanism: it's *how* the OS makes sure it gets the CPU back. *How long* to let each user program run before the timer goes off is a policy decision. Same mechanism, many possible policies:

- 10 ms for every program,
- longer slices for background jobs,
- shorter slices for interactive programs so they feel snappy.

## Why separate them?

**Policies change.** They differ from place to place and over time. If every policy change meant rewriting a mechanism, the OS would be brittle. Keep them separate, and the system gets **maximum flexibility when policy decisions change later**: you just adjust a parameter.

The ideal is a **general mechanism** that works for a whole range of policies.

## More examples

| Mechanism (how) | Policy (what) |
|---|---|
| A way to give a process priority over others | Should I/O-heavy programs get priority over CPU-heavy ones? |
| A way to check file permissions on every access | Who is allowed to read the payroll file? |
| A way to evict a page from memory | Which page should be evicted? |
| A way to lock the screen | Lock after 5 minutes idle, or 30? |

Microkernels (Part 7) push this idea far: the kernel keeps a few basic mechanisms, and policies live in user-space programs that can be swapped.

Finally, **specifying and designing an OS is a highly creative task of software engineering**. Principles like this one help, but they don't write the system for you.

A check on policy and mechanism.
