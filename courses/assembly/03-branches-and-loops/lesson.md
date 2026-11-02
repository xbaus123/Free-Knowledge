# Assembly: Branches and Loops

Assembly has no `if`, `for`, or `while`. Instead, the CPU keeps **flags** describing the result of the last arithmetic or comparison, and **jump** instructions go to a label depending on those flags.

## Compare, then jump

`cmp a, b` subtracts `b` from `a`, throws away the result, and sets the flags. A conditional jump right after it reads them:

| Jump  | Jumps if (signed)  |
| ----- | ------------------ |
| `je`  | `a == b`           |
| `jne` | `a != b`           |
| `jl`  | `a < b`            |
| `jle` | `a <= b`           |
| `jg`  | `a > b`            |
| `jge` | `a >= b`           |

`jmp` always jumps. Unsigned values use different jumps (`jb`, `ja` for "below" and "above"), because the same bits mean different numbers: `-1` is also the largest unsigned 64-bit value.

Here is `if (x < 0) x = -x; return x;`:

```asm
absolute:
    mov rax, rdi
    cmp rax, 0
    jge absolute_done   # skip the negation when x >= 0
    neg rax
absolute_done:
    ret
```

Labels must be unique within a file, so prefix them with the function's name.

## Loops

A loop is a jump backwards. This counts `rcx` from 0 up to `n` (in `rdi`) and adds each value to `rax`:

```asm
    xor eax, eax        # rax = 0 (xor with itself is the usual idiom)
    xor ecx, ecx        # i = 0
count_loop:
    cmp rcx, rdi
    jge count_done      # stop when i >= n
    add rax, rcx
    inc rcx
    jmp count_loop
count_done:
    ret
```

Checking the condition at the top means the body never runs when `n` is 0.

## Reading memory

Square brackets read memory at an address. Since a `long` is 8 bytes, element `i` of an array starting at `rdi` is at `rdi + i * 8`, and x86 can compute that inside the instruction:

```asm
    mov rdx, [rdi + rcx*8]   # rdx = xs[i]
    add rax, [rdi + rcx*8]   # rax += xs[i]
```

## Your task

Implement in `starter.s`:

1. `long max2(long a, long b)` returns the larger of `a` and `b`.
2. `long sum_array(const long *xs, long n)` returns the sum of the `n` values in `xs`. An empty array (`n` is 0) sums to 0.
