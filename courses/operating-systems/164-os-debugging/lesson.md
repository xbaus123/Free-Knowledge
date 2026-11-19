# Debugging an Operating System

*Chapter 2 · Part 8: Debugging, Generation, and Boot.*

**Debugging** is finding and fixing errors, or **bugs**. Debugging an OS is harder than debugging an app: the thing that crashed is the thing that normally helps you debug.

## What the OS leaves behind

| When... | The OS produces... | Containing... |
|---|---|---|
| Something goes wrong, at any time | **Log files** | Error information, written as it happens |
| An **application** fails | A **core dump** file | **The memory of the process** at the moment it died |
| The **operating system itself** fails | A **crash dump** file | **Kernel memory** |

A **core dump** lets a programmer load the dead process's memory into a debugger afterward and see exactly what it was doing. (The name goes back to *magnetic core* memory, from the earliest days of computing.)

A **crash dump** is trickier. When the kernel crashes, its own file-system code might be the broken part, so it can't safely write a normal file. Systems often save kernel memory to a **reserved area of the disk** that needs no file system, then recover it into a file on the next boot.

## Kernighan's Law

Brian Kernighan (co-author of *The C Programming Language*) made a famous observation about debugging. Paraphrased: **debugging is twice as hard as writing the code in the first place, so if you write code as cleverly as you possibly can, you are, by definition, not smart enough to debug it.**

The lesson for OS writers, who debug the hardest code there is: **write clearly, not cleverly.**

## Beyond crashes

Debugging isn't only about crashes. **Performance problems** are bugs too, and the next lesson covers how to find them.

A check on OS debugging.
