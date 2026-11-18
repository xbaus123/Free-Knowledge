# A Dual-Mode Machine in Python

*Chapter 1 · Part 4: Operating-System Structure and Operations.*

You've read how the hardware keeps the OS in charge: a **mode bit**, **privileged instructions**, **system calls**, and a **timer**. Now you'll build a toy machine that enforces all four, and watch it stop misbehaving programs.

## The machine

`Machine` has three attributes:

- `mode`: `KERNEL` (0) or `USER` (1). A new machine **starts in kernel mode**, since the OS is in control before any user program runs.
- `timer`: the timer's counter. `0` means the timer isn't set.
- `log`: a list of strings recording every interrupt, trap, and system call, in order.

## A program

A user program is a list of instruction strings:

| Instruction | Meaning |
|---|---|
| `"add"`, `"load"`, `"store"`, … | An ordinary instruction. Anything not listed below is ordinary. |
| `"syscall:read"` | A system call named `read` (any name after the colon) |
| `"div0"` | A division by zero |
| A name in `PRIVILEGED` | A privileged instruction, like `"set_timer"` or `"io"`. It may also carry an argument after a colon, like `"io:disk0"`. |

## Your task

1. **`is_privileged(instruction)`**: is the part before any `:` in `PRIVILEGED`?
2. **`set_timer(ticks)`**: setting the timer is itself privileged. In user mode, raise `PermissionError`. In kernel mode, set `self.timer`.
3. **`run(program)`**: the kernel hands the CPU to a user program. It must be called in kernel mode (raise `PermissionError` otherwise). Switch to **user mode**, then go through the instructions one by one:
   - **Privileged instruction** (in user mode): don't execute it. Trap: switch to kernel mode, log `"trap:illegal:<instruction>"`, and return `("killed", n)`.
   - **`"div0"`**: trap: switch to kernel mode, log `"trap:divide-by-zero"`, return `("killed", n)`.
   - **`"syscall:<name>"`**: switch to kernel mode, call `self.handle_syscall(name)` (it's written for you; it logs `"syscall:<name>"`), then switch back to user mode.
   - **Anything else**: an ordinary instruction; just execute it (nothing to do).

   Here `n` is how many instructions **completed**. The instruction that traps doesn't count; ordinary instructions and system calls do.

   **The timer:** after each completed instruction, if the timer is set (greater than 0), decrement it by one. If that makes it reach 0, the timer interrupts: switch to kernel mode, log `"interrupt:timer"`, and return `("timer", n)`.

   If the program runs out of instructions, switch to kernel mode, log `"exit"`, and return `("done", n)`.

Whatever happens, **`run` always returns with the machine in kernel mode**. That's the whole point: the OS ends up in control.

## An example

```python
m = Machine()
m.set_timer(3)
m.run(["load", "syscall:write", "add", "add", "store"])
# -> ("timer", 3); m.log == ["syscall:write", "interrupt:timer"]; m.mode == KERNEL
```

Use **Run** to try things out, and **Submit** to run the tests.
