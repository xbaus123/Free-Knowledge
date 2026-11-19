# Loadable Kernel Modules

*Chapter 2 · Part 7: Operating-System Structure.*

Many modern operating systems take a middle road: **loadable kernel modules (LKMs)**.

## The idea

- It uses an **object-oriented approach**.
- **Each core component is separate.**
- **Each talks to the others over known interfaces.**
- **Each is loadable as needed within the kernel.**

The kernel has a small core. Extra pieces, like a driver for a new USB device or support for a new file system, are **linked into the running kernel when needed**, either at boot or while the system is running. No rebuild, no reboot.

## Solaris

Solaris organizes its kernel around a **core kernel** with **seven types of loadable modules**:

```
            scheduling classes
   device and           |          file systems
   bus drivers  \       |        /
                  [ core Solaris ]
  miscellaneous --[    kernel    ]-- loadable system calls
     modules      /            \
         STREAMS modules    executable formats
```

1. Scheduling classes
2. File systems
3. Loadable system calls
4. Executable formats
5. STREAMS modules
6. Miscellaneous
7. Device and bus drivers

## Like layers, but more flexible

Modules are **similar to layers, but more flexible**: any module can call any other through its interface, not just the ones "below" it. And they're like a microkernel in that the core stays small, **but without the message-passing cost**: modules run **inside the kernel**, so they call each other directly.

**Linux and Solaris** both use loadable modules. On Linux you can see them with `lsmod`, add one with `modprobe`, and remove one with `rmmod`.

| | Layers | Microkernel | Modules |
|---|---|---|---|
| Who can call whom | Only lower layers | Anyone, via messages | Anyone, via known interfaces |
| Where services run | Kernel | **User space** | **Kernel** |
| Communication cost | A crossing per layer | High (messages) | Low (function calls) |

A check on modules.
