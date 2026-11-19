# What Services Does an OS Provide?

*Chapter 2 · Part 1: Operating-System Services.*

Chapter 1 asked what an operating system *is*. Chapter 2 asks a builder's questions: **what does it offer, how do programs ask for it, and how is the thing put together inside?**

Start with the offer. An operating system provides **an environment for executing programs**, plus a set of **services** to programs and to the users of those programs.

## Two families of services

The services split into two groups, depending on who they're mainly for:

| Helpful to the **user** | Keep the **system itself** running efficiently |
|---|---|
| User interface | Resource allocation |
| Program execution | Accounting |
| I/O operations | Protection and security |
| File-system manipulation | |
| Communications | |
| Error detection | |

The left column is what you'd miss as a user or programmer. The right column is what the system needs when **many users and many jobs share one machine**.

## Where the services sit

```
        user and other system programs
   [   GUI   |   batch   |   command line   ]   user interfaces
   [ ............ system calls ............ ]
   [ program  I/O   file     comm-   resource  accounting ]
   [ exec     ops   systems  unication allocation          ]
   [    error detection     protection and security       ]  services
   [               operating system                        ]
   [                  hardware                             ]
```

Notice the layer called **system calls**. Every service below it is reached *through* it. Programs never jump straight into the OS; they make a system call, and Part 3 shows exactly how.

Next, a short check before we look at each user-facing service.
