# Assembly: The Stack

Sixteen registers run out quickly. The **stack** is a region of memory every program gets for temporary values, and the `rsp` register ("stack pointer") always holds the address of its top.

## Push and pop

The stack grows **down** toward lower addresses, 8 bytes at a time:

| Instruction | Effect                                         |
| ----------- | ---------------------------------------------- |
| `push rax`  | `rsp -= 8`, then store `rax` at `[rsp]`        |
| `pop rax`   | load `[rsp]` into `rax`, then `rsp += 8`       |

The last value pushed is the first popped, so pushing values and popping them back gives them to you in reverse order:

```asm
    push rdi        # stack: a
    push rsi        # stack: a, b
    pop rdi         # rdi = b
    pop rsi         # rsi = a   (swapped!)
```

Both also work directly on memory, as in `push qword ptr [rdi + rcx*8]`, where `qword ptr` says the value is 8 bytes (a "quad word").

Every push needs a matching pop before `ret`, because `ret` itself pops the stack.

## Call and return

`call f` pushes the address of the next instruction (the **return address**) and jumps to `f`. `ret` pops that address and jumps back to it. This is why a function that leaves an extra value on the stack crashes when it returns: `ret` jumps to the wrong place.

## Saving registers

The calling convention splits registers in two:

- **Caller-saved:** `rax`, `rcx`, `rdx`, `rsi`, `rdi`, `r8` to `r11`. Any function you call may overwrite them.
- **Callee-saved:** `rbx`, `rbp`, `r12` to `r15`. A function must leave them as it found them.

To keep a value safe across a `call`, put it in a callee-saved register, and save that register's old value on the stack first:

```asm
twice_plus_one:
    push rbx            # rbx belongs to our caller: save it
    mov rbx, rdi
    call helper         # helper may overwrite rdi, but not rbx
    add rax, rbx
    pop rbx             # restore it for our caller
    ret
```

One more rule: the stack pointer must be a multiple of 16 when you `call` a function. On entry to yours it's 8 bytes off (the return address), so an odd number of pushes before a `call` lines it up, as the single `push rbx` above does.

## Your task

Implement in `starter.s`:

1. `void reverse(long *xs, long n)` reverses the `n` values in `xs` in place. Push every value onto the stack in one loop, then pop them back into the array from the start in a second loop.
2. `long square(long x)` returns `x * x`.
3. `long sum_of_squares(long a, long b)` returns `a * a + b * b` by calling your `square` twice. `b` has to survive the first call and `a * a` the second, so keep each in a callee-saved register while `square` runs. One register can hold them in turn.

The tests check that `rbx`, `rbp`, `rsp`, and `r12` to `r15` come back unchanged from every function.
