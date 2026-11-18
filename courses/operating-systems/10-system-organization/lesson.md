# Computer-System Organization

*Chapter 1 · Part 2: Computer-System Organization.*

Once the kernel is running, what is it actually managing? A modern computer looks like this:

```
          disks       mouse keyboard printer     monitor
            |            \     |     /              |
 [ CPU ] [ disk     ] [   USB controller   ] [ graphics ]
   |     [controller]           |            [ adapter  ]
   |         |                  |                 |
 ──┴─────────┴──────────────────┴─────────────────┴──── common bus
                          |
                     [ memory ]
```

## The pieces

- **One or more CPUs** and several **device controllers** connect through a **common bus** that gives them access to **shared memory**.
- Each **device controller** is in charge of **one particular type of device**: a disk controller, a USB controller, a graphics adapter. A single controller may handle several devices (the USB controller above runs a mouse, keyboard, and printer).
- Each device controller has a **local buffer**: a bit of its own storage, plus some special registers.

## Everything runs at once

The CPUs and the devices **execute concurrently**. While the CPU runs your program, the disk controller can be reading a block and the network card can be receiving a packet. They all **compete for memory cycles** on the shared bus.

## Who moves the data?

- **I/O** goes from the **device to the controller's local buffer** (or back).
- The **CPU** moves data **between main memory and those local buffers**.
- When a controller finishes its operation, it tells the CPU by causing an **interrupt** (next lesson).

## Device drivers

For each device controller, the OS has a **device driver**: code that understands that controller and gives the rest of the kernel a **uniform interface** to it. The kernel says "read block 7"; the driver knows which registers on *this* disk controller make that happen. That's how one OS supports thousands of different devices.

Next, a check on how the hardware is organized.
