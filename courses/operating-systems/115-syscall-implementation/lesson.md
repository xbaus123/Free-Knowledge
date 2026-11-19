# How a System Call Gets to the Kernel

*Chapter 2 · Part 3: System Calls.*

You call `open()`. How does the kernel know what you want?

## A number for every call

Typically, **a number is associated with each system call**. The **system-call interface** keeps a **table indexed by these numbers**. Each entry points at the kernel code that implements that call.

```
      user application
            |  open()
  ----------v------------------------------  user mode
        system call interface
  ----------|------------------------------  kernel mode
            v
        +-------+
        |  ...  |
      i | open -+------->  implementation of open()
        |  ...  |                 ...
        +-------+              return  ----> back up through the
         table                                 interface to the app
```

1. The program calls the API function `open()`.
2. The library puts system-call number *i* (and the parameters) where the kernel expects them, and traps.
3. The system-call interface, now in **kernel mode**, looks up entry *i* in the table and **invokes the intended system call**.
4. When it's done, the interface **returns the status of the call and any return values** to the program, back in user mode.

## The caller knows nothing

**The caller need know nothing about how the system call is implemented.** It just obeys the API and understands what the OS will do. Most of the details of the OS interface are hidden by the API and handled by the **run-time support library**: a set of functions built into the libraries included with the compiler.

## Example: printf()

A C program calls `printf("Greetings")`. That's not a system call; it's a **library call** in the **standard C library**. The library formats the text, then calls the **`write()` system call** to actually put it on the screen:

```
 user mode    main() ---> printf()  [standard C library]
 -------------------------------------|---------------------
 kernel mode                       write()  system call
```

Then control returns up through the library to your program.

A check on the path from API to kernel.
