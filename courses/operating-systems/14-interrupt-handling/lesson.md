# Handling an Interrupt

*Chapter 1 · Part 2: Computer-System Organization.*

You've seen *what* an interrupt does. Now let's follow one through, step by step, and see how the CPU and an I/O device share the timeline.

## The steps

1. **Save the state.** The OS preserves the state of the CPU by **storing the registers and the program counter**. The interrupted program must be able to continue exactly where it was.
2. **Work out which interrupt happened.** There are two ways:
   - **Polling**: ask each device in turn, "was it you?" Simple, but slow when there are many devices.
   - **Vectored interrupt system**: the interrupting device sends a number along with the interrupt, and the CPU jumps through the interrupt vector to the right routine. Fast.
3. **Run the right code.** Separate segments of code decide what to do for each type of interrupt: copy a disk block, record a keypress, wake a waiting program.
4. **Restore the state** and return to the interrupted program.

## The interrupt timeline

Here's one user program doing two I/O requests:

```
CPU     user process executing ███████▁▁████████████████▁▁█████
        I/O interrupt processing      ██                ██
I/O     idle            ████          ████████████      ██████
device  transferring        ████████              ██████
                       ↑           ↑            ↑      ↑
                  I/O request  transfer done  request  done
```

Read it left to right:

1. The program makes an **I/O request**. The device starts **transferring**, and the CPU **keeps running the user program**.
2. When the **transfer is done**, the device raises an interrupt. The CPU briefly switches to **I/O interrupt processing**, then goes back to the user process.
3. The same happens for the second request.

The CPU spends only a sliver of time on the interrupt. For the rest, CPU and device work **in parallel**. That overlap is the whole point.

Next, a check on interrupt handling.
