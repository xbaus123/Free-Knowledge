# Passing Parameters to the OS

*Chapter 2 · Part 3: System Calls.*

Knowing *which* system call isn't enough. `read()` also needs a file descriptor, a buffer, and a count. The exact type and amount of information **vary by OS and by call**. How do the parameters get to the kernel?

## Three general methods

**1. In registers.** The simplest: put the parameters in CPU registers before trapping.
*Problem:* sometimes there are **more parameters than registers**.

**2. In a block (table) in memory.** Store the parameters in a block of memory, and pass the **address of the block** in a register. **Linux and Solaris** take this approach (Linux uses registers when there are few enough parameters, and a block otherwise).

```
   user program                         operating system
  +--------------------+              +-----------------------+
  | X: parameters      |   register   |                       |
  |    for call        |   +-----+    | code for              |
  | load address X  ---+-->|  X  |--->| system call 13:       |
  | system call 13  ---+---------------> use parameters       |
  +--------------------+   +-----+    |   from table X        |
                                      +-----------------------+
```

**3. On the stack.** The program **pushes** the parameters onto the **stack**; the operating system **pops** them off.

## Comparing them

| Method | Limit on number or size of parameters? |
|---|---|
| Registers | **Yes**: only as many as there are registers |
| Block in memory | **No** |
| Stack | **No** |

Block and stack methods **don't limit the number or length of parameters** being passed. That's why systems fall back to them when registers run out.

A check on parameter passing, then you'll build a system-call table.
