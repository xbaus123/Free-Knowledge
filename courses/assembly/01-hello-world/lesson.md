# Assembly: Hello, World

Assembly is the last human-readable step before machine code: each line is one instruction the CPU runs. This course writes **x86-64** assembly (the instruction set of most PCs and Intel Macs) for the **GNU assembler**, the same tool `gcc` and `clang` use, in **Intel syntax**.

> **Before you start:** your computer needs `gcc` or `clang`. On an Apple Silicon Mac the code is built for x86-64 and runs under Rosetta; if it isn't installed, run `softwareupdate --install-rosetta`. ARM Linux machines can't run these lessons.

## Anatomy of a function

```asm
    .intel_syntax noprefix   # write "mov rax, 1", not "movq $1, %rax"
    .text                    # what follows is code

    .globl answer            # make the label visible to other files
answer:                      # a label names an address: here, the function
    mov eax, 42              # put 42 in the return register
    ret                      # return to whoever called us
```

- Lines starting with `.` are **directives**: instructions to the assembler, not the CPU.
- `answer:` is a **label**. Calling `answer` jumps to the instruction right after it.
- `mov dest, src` copies a value. In Intel syntax the destination always comes first.
- A function returns its result in the **`rax`** register (`eax` is its lower 32 bits; more on that next lesson). `ret` jumps back to the caller.
- Comments start with `#`. Careful: tutorials for other assemblers use `;`, which here separates two instructions on one line.

## Data

Strings live in memory, not in registers. The `.data` directive switches to a section for data, and `.asciz` stores the bytes of a string followed by a zero byte, which is how C marks the end of a string:

```asm
    .data
name:
    .asciz "Ada"
```

A function that returns a string returns its **address**. `lea` ("load effective address") computes an address without reading memory, and `[rip + name]` means "the address of `name`, relative to this instruction", which works wherever the program is loaded:

```asm
    lea rax, [rip + name]    # rax = address of "Ada"
```

Switch back to `.text` before writing more code.

## Your task

Complete `starter.s`:

1. `answer` returns `42`.
2. `greeting` returns the string `"Hello, World!"`. Define it in a `.data` section and return its address with `lea`.

The tests are written in C and call your functions as `long answer(void)` and `const char *greeting(void)`. Don't write a `main` function; the tests provide one.
