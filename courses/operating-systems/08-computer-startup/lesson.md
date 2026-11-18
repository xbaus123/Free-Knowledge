# Computer Startup

*Chapter 1 · Part 2: Computer-System Organization.*

When you press the power button, memory is empty. There's no OS loaded yet, so who loads it? This part of the chapter looks at the hardware the OS runs on, starting at the very first instant.

## The bootstrap program

At power-up or reboot, the CPU starts running a small program called the **bootstrap program**. It lives somewhere that survives power loss:

- Traditionally **ROM** (read-only memory) or **EEPROM** (electrically erasable programmable ROM).
- Code stored in hardware like this is called **firmware**: software that's baked into the machine rather than loaded from disk.

## What the bootstrap does

1. **Initializes all aspects of the system**: CPU registers, device controllers, the contents of memory.
2. **Finds the operating system kernel** on disk.
3. **Loads the kernel into memory and starts executing it.**

From then on, the kernel is in charge.

```
 power on → bootstrap program (firmware, in ROM/EEPROM) → loads kernel → kernel runs
```

Next, a short check on startup.
