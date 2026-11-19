# Chapter 2 Complete

*Chapter 2 · Wrap-Up.*

That's the inside of the machine's organizer. You can now:

- **List what an OS offers**: user interfaces, program execution, I/O, file systems, communications, and error detection for users; resource allocation, accounting, and protection and security for the system.
- **Explain how people talk to it**: command interpreters and shells, built-in commands versus program names, GUIs, touchscreens, and batch. You built a shell that runs both.
- **Trace a system call** from an API like POSIX through the C library and a trap to the system-call table and back, and pass its parameters in registers, a memory block, or on the stack. You built that table.
- **Sort system calls into their six categories**, and match Windows and UNIX names, from `CreateProcess()` and `fork()` to `SetFileSecurity()` and `chmod()`.
- **Tell system programs, daemons, and applications apart**, and explain why most users see the OS through its system programs.
- **Reason about design**: user and system goals, policy versus mechanism, and why kernels are written mostly in C.
- **Compare structures**: simple, monolithic, layered, microkernel, modules, and hybrids, down to macOS, iOS, and Android. You measured why layers are hard to define and why microkernels pay for their messages.
- **Debug and tune a system** with logs, core and crash dumps, profiling, and DTrace, and you built a profiler.
- **Follow a machine from power-on to running**: firmware, boot block, bootstrap loader, kernel, plus how SYSGEN fits an OS to its hardware.

Next up is the thing every one of these structures exists to run: the **process**.

**Chapter 2 complete.**
