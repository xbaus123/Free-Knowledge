# Microkernels

*Chapter 2 · Part 7: Operating-System Structure.*

The opposite of monolithic: **move as much as possible out of the kernel and into user space**.

## The idea

A **microkernel** keeps only the essentials in kernel mode, typically:

- **Interprocess communication (IPC)**
- **Memory management** (the basics)
- **CPU scheduling**

Everything else (**file systems, device drivers**, network stacks) runs as ordinary **user-mode processes**.

```
  +-------------+    +-------------+    +-------------+
  | Application |    |    File     |    |   Device    |    user
  |   Program   |    |   System    |    |   Driver    |    mode
  +------^------+    +---^-----^---+    +------^------+
         :   messages    :     :   messages    :
  -------:---------------:-----:---------------:--------------
  |  [ Interprocess ]  [  memory   ]   [   CPU      ]          |  kernel
  |  [Communication ]  [ management]   [ scheduling ]          |  mode
  |                      microkernel                           |
  --------------------------------------------------------------
                          hardware
```

## How parts talk: message passing

With the file system in its own process, an application can't just call it. **Communication between user modules takes place through message passing**, and the microkernel delivers the messages. To read a file, the app sends a message (through the kernel) to the file-system process, which may message the disk-driver process (through the kernel), and the answers come back the same way.

## Mach and Darwin

**Mach**, from Carnegie Mellon University in the 1980s, is the classic microkernel. The **macOS kernel, Darwin, is partly based on Mach**.

## Benefits

- **Easier to extend**: a new service is a new user-space program; the kernel doesn't change.
- **Easier to port** to new architectures: there's less kernel to port.
- **More reliable**: **less code is running in kernel mode**. If a driver crashes, it's just a process; it can be restarted while the rest of the system keeps going.
- **More secure**: a bug in the file system can't scribble on kernel memory.

## Detriment

- **Performance overhead of user-space-to-kernel-space communication.** Every message means system calls and mode switches. What a monolithic kernel does with one function call, a microkernel does with several messages.

That cost is real: early versions of Windows NT were built as a microkernel and moved services back into the kernel for speed.

A check on microkernels.
