# Assembly: Registers and Arithmetic

The CPU does its work in **registers**: 16 small, fast storage slots of 64 bits each, named `rax`, `rbx`, `rcx`, `rdx`, `rsi`, `rdi`, `rbp`, `rsp`, and `r8` to `r15`.

## Smaller views of the same register

Each register can also be used at narrower widths. They aren't separate registers: `eax` *is* the low half of `rax`.

| 64 bits | 32 bits | 16 bits | 8 bits |
| ------- | ------- | ------- | ------ |
| `rax`   | `eax`   | `ax`    | `al`   |
| `rdi`   | `edi`   | `di`    | `dil`  |
| `r8`    | `r8d`   | `r8w`   | `r8b`  |

Writing a 32-bit register clears the upper 32 bits of the full register, so `mov eax, 42` leaves `rax` holding exactly 42. Writing 8 or 16 bits leaves the rest untouched, so to widen a small value use `movzx` ("move with zero extension"):

```asm
    movzx eax, dil     # rax = the low byte of rdi, zero-extended
```

## The calling convention

Assembly has no named parameters. Instead, the caller and callee agree on where arguments go: the **System V calling convention**, used on Linux and macOS (and by these lessons everywhere). The first six integer or pointer arguments arrive in

```
rdi, rsi, rdx, rcx, r8, r9
```

and the result goes back in `rax`. So `long add(long a, long b)` finds `a` in `rdi` and `b` in `rsi`:

```asm
add:
    mov rax, rdi       # rax = a
    add rax, rsi       # rax += b
    ret
```

## Arithmetic

Most arithmetic instructions take two operands and overwrite the first:

| Instruction    | Effect                        |
| -------------- | ----------------------------- |
| `add rax, rsi` | `rax = rax + rsi`             |
| `sub rax, rsi` | `rax = rax - rsi`             |
| `imul rax, rsi`| `rax = rax * rsi` (signed)    |
| `neg rax`      | `rax = -rax`                  |
| `inc rax`      | `rax = rax + 1`               |

`rax`, `rcx`, `rdx`, `rsi`, `rdi`, and `r8` to `r11` are yours to overwrite freely inside a function. The others (`rbx`, `rbp`, `rsp`, and `r12` to `r15`) belong to the caller and must hold the same values when you return; the stack lesson shows how to borrow them. The tests check this.

## Your task

Implement in `starter.s`:

1. `long linear(long a, long x, long b)` returns `a * x + b`.
2. `long low_byte(long x)` returns the lowest 8 bits of `x` as a number from 0 to 255. For example, `low_byte(0x1234)` is `0x34`.
