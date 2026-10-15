# Understanding Compilers

You've now run code in five languages, but they didn't all run the same way. Python and JavaScript started almost instantly. Go, C, and Rust paused for a moment first. That pause was a **compiler** at work.

## Translating for the machine

A CPU only understands **machine code**: numbered instructions like "load this value" or "add these two registers". Nobody wants to write that by hand, so we write source code and let a program translate it.

A **compiler** translates the whole program ahead of time and produces an executable file. When you ran the C lesson, `gcc` turned `solution.c` into a binary, and only then did the tests run. The result starts fast and runs fast, because the translation work is already done.

An **interpreter** reads your program and carries it out as it goes. Python works this way (strictly, it first compiles to a simpler *bytecode* that its interpreter runs). You get quick feedback and can run code line by line, at the cost of slower execution.

## What compilers catch

Because a compiler reads your whole program before running any of it, it can reject mistakes early. A missing semicolon in C, or passing a string where Rust expects a number, fails at **compile time**, before any test runs. In Python, the same kinds of mistakes usually surface at **run time**, only when that line actually executes.

Many modern runtimes blur the line. Node.js uses a **just-in-time (JIT)** compiler: it starts by interpreting JavaScript, then compiles the hot parts of your program to machine code while it runs.

## Why it matters

Knowing whether your language is compiled or interpreted explains a lot: why some errors appear before your program starts, why Go programs ship as a single file, and why a tight loop runs faster in Rust than in Python.

When you're ready, mark this lesson complete and test what you know in the next one.
