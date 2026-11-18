# Dual-Mode Operation

*Chapter 1 · Part 4: Operating-System Structure and Operations.*

If any program could run any instruction, a buggy program could turn off interrupts, overwrite the kernel, or talk straight to the disk. The OS needs a way to **protect itself and the other system components**. The hardware provides it: **dual-mode operation**.

## Two modes

The CPU runs in one of two modes:

- **User mode**: for running user programs.
- **Kernel mode**: for running the operating system.

## The mode bit

A **mode bit** provided by the hardware records the current mode:

| Mode | Mode bit |
|---|---|
| **Kernel** | **0** |
| **User** | **1** |

The mode bit lets the hardware **tell whether it's running user code or kernel code**.

## Privileged instructions

Some instructions are designated **privileged**: they can **only be executed in kernel mode**. Setting the timer (next lesson) is one. Think of the instructions that could hurt other programs or the OS if anyone could run them: setting the mode bit, controlling I/O devices directly, turning interrupts off.

If a user-mode program tries a privileged instruction, it isn't allowed to run: the hardware **traps to the OS** instead.

## Crossing the line: system calls

So how does a user program get anything done that needs privilege, like reading a file? It makes a **system call**.

```
 user mode    user process executing → calls system call            return from system call
 (bit = 1)                                     │                                ▲
 ─────────────────────────────────────────────┼────────────────────────────────┼──────
 kernel mode                         trap, mode bit = 0      return, mode bit = 1
 (bit = 0)                                     └──► execute system call ────────┘
```

1. The program calls a system call. That causes a **trap**, which sets the mode bit to **0** (kernel).
2. The kernel checks the request is legal, then **executes the system call**.
3. On return, the mode bit is set back to **1** (user), and the program continues.

Every interrupt or trap switches to kernel mode, so **the OS is in control whenever anything important happens**.

## More than two modes

**Increasingly, CPUs support more than two modes.** For example, a **virtual machine manager (VMM)** mode lets a VMM control **guest VMs**: more privileged than a guest OS's kernel.

Next, a check on dual-mode operation.
