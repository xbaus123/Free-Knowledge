# Virtualization

*Chapter 1 · Part 7: Computing Environments.*

**Virtualization** allows **operating systems to run applications within other operating systems**: Windows running in a window on a Mac, or a hundred Linux machines on one physical server. It's a **vast and growing industry**.

## Emulation vs virtualization

These sound alike but work differently:

- **Emulation** is used **when the source CPU type is different from the target type**: for example, running **PowerPC** software on an **Intel x86** CPU. The emulator translates every instruction from one CPU's language to the other's. It's **generally the slowest method**.
  - A close relative: when a computer language isn't compiled to native code at all, but run by a program that reads it, that's **interpretation**.
- **Virtualization** is when **an OS natively compiled for the CPU** runs **guest OSes that are also natively compiled** for it. No translation: the guests' instructions run directly on the real CPU.
  - Example: **VMware** running several **Windows XP guests**, each running applications, all on a native **Windows XP host** OS.
  - The **VMM** (**virtual machine manager**) provides the virtualization services.

## The picture

```
      (a) no virtualization              (b) virtualization
 ┌──────────────────────┐   ┌───────────┬───────────┬───────────┐
 │      processes       │   │ processes │ processes │ processes │
 ├──────────────────────┤   ├───────────┼───────────┼───────────┤
 │        kernel        │   │  kernel   │  kernel   │  kernel   │
 ├──────────────────────┤   │   VM1     │   VM2     │   VM3     │
 │       hardware       │   ├───────────┴───────────┴───────────┤
 └──────────────────────┘   │    virtual machine manager        │
                            ├───────────────────────────────────┤
                            │            hardware               │
                            └───────────────────────────────────┘
```

In (a), processes use the kernel's **programming interface**, and the kernel runs the hardware. In (b), each **VM** has its own kernel, and the **VMM** sits between those kernels and the real hardware. Each guest kernel thinks it has a machine to itself.

## Use cases

Laptops and desktops running **multiple OSes for exploration or compatibility**:

- An **Apple laptop** running **macOS as host** and **Windows as a guest**.
- **Developing apps for multiple OSes** without having multiple systems.
- **QA testing** applications without having multiple systems.
- **Executing and managing compute environments within data centers**.

## The VMM as the host

A VMM can also **run natively**, directly on the hardware, in which case **it is also the host**. Then **there's no general-purpose host OS** at all. Examples: **VMware ESX** and **Citrix XenServer**.

Next, a check on virtualization.
