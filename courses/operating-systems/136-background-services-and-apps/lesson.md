# Background Services and Applications

*Chapter 2 · Part 5: System Programs.*

Two more kinds of program round out the picture.

## Background services

Some system programs **launch at boot time** and run without anyone asking:

- Some handle **system startup and then terminate**.
- Others run **from system boot to shutdown**.

They provide facilities like **disk checking, process scheduling, error logging, and printing**. A web server waiting for connections, a print spooler waiting for jobs, and a program that syncs the clock are all examples.

Key facts:

- They **run in user context, not kernel context**. They're ordinary processes, not part of the kernel.
- They're known as **services**, **subsystems**, or **daemons**. In UNIX their names often end in "d": `sshd`, `httpd`, `crond`, `launchd`.

A typical system has **dozens** of daemons running at any moment.

## Application programs

At the top are **application programs**:

- They **don't pertain to the system**: web browsers, word processors, spreadsheets, games, databases.
- They're **run by users**.
- They're **not typically considered part of the OS**.
- They're **launched by command line, mouse click, or finger poke**.

## The whole stack, so far

```
   application programs           (browsers, games, editors)
   system programs and daemons    (shells, compilers, ls, sshd)
   ---------- system calls ----------
   kernel
   hardware
```

Where exactly the line falls between "system program" and "application" is fuzzy. Is a web browser part of the OS? That question was once the center of a major antitrust case against Microsoft. The usual answer is no.

A check, then a drill.
