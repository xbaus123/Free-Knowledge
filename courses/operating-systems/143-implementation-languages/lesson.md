# Implementation: What Is an OS Written In?

*Chapter 2 · Part 6: Design and Implementation.*

Once it's designed, an OS has to be written in *something*. **There's been much variation.**

## A short history

| Era | Language |
|---|---|
| Early operating systems | **Assembly language** |
| Then | **System programming languages** like **Algol** and **PL/1** |
| Now | **C and C++** |

## Actually, a mix

Real systems are **usually a mix of languages**:

- **The lowest levels in assembly**: the code that runs right at boot, saves registers on an interrupt, or switches between processes needs exact control of the CPU.
- **The main body in C**: Linux and Windows kernels are mostly C.
- **System programs in C, C++, and scripting languages** like **Perl, Python, and shell scripts**.

## High level versus low level

| High-level language | Assembly |
|---|---|
| **Easier to port** to other hardware: recompile instead of rewrite | Tied to one CPU's instruction set |
| Faster to write, easier to read and debug | Tedious to write |
| **But slower** (in principle) | Can be hand-tuned for speed |

**Port** means moving an OS to new hardware. An OS written in C can run on a new CPU mostly by recompiling it; one written in assembly has to be rewritten. Linux runs on everything from watches to supercomputers largely because it's in C.

The "slower" cost is smaller than it sounds. Modern compilers are very good, and the biggest performance wins come from **better data structures and algorithms**, not hand-written assembly. Usually only a small amount of code is critical to performance, and that can be tuned separately.

## Emulation

**Emulation** can allow an OS to **run on non-native hardware**: software imitates one CPU on top of another. It's how old game consoles run on modern PCs, and how an OS built for one architecture can be tested on another before real chips exist. The price is speed, since every emulated instruction takes many real ones.

A check on implementation.
