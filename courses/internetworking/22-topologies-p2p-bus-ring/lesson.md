# LAN Topologies: Point-to-Point, Bus, and Ring

*Chapter 2 · Topologies and the Physical Layer.*

A network's **topology** is its shape: which devices connect to which. It decides what breaks when one cable fails, how easy the network is to grow, and how much it costs to wire.

There are two views of the same network:

- **Physical topology**: how the cables actually run.
- **Logical topology**: how data actually flows. A network can be wired as a star and still pass data around in a ring.

This lesson covers the three simplest shapes. The next covers star, mesh, and tree.

## Point-to-point

```
   [A] ─────────────── [B]
```

Two devices joined by **one dedicated link**. Nothing else shares it, so all of its capacity belongs to those two.

- **Typically peer-to-peer**: two computers, or two routers, talking straight to each other.
- Often a single **twisted-pair** cable (more on that cable later in this chapter).
- As simple as networking gets, but it only connects two things. Every other shape is built out of links like this.

## Bus

```
   [A]      [B]      [C]      [D]
    │        │        │        │
 ■──┴────────┴────────┴────────┴──■
 terminator        backbone       terminator
```

Every device taps into **one shared cable**, the **backbone** or **bus**. A signal sent by one device travels along the whole cable, and every device hears it. A **terminator** at each end absorbs the signal so it doesn't bounce back.

- **Low cost**: one cable, no central device.
- **Hard to troubleshoot**: when it stops working, the fault could be anywhere along the cable, and one break or missing terminator takes down **the whole bus**.
- Only one device can send at a time. If two send at once, their signals **collide**, so a busy bus gets slow.

Early Ethernet ran on a coaxial bus. You'll rarely see one today.

## Ring

```
        [A] ──── [B]
         │        │
        [D] ──── [C]
```

Each device connects to exactly **two neighbors**, forming a closed loop. Data travels around the ring in one direction, and each device passes it along until it reaches its destination.

Classic rings use **token passing**: a special message called the *token* circulates, and only the device holding it may send. Nobody talks over anybody else.

- **Good quality**: no collisions, and every device gets a fair, predictable turn.
- **Limited scalability**: every device added is one more hop that each message must pass through, so a big ring gets slow. Adding or removing a device also means opening the ring.
- In a single ring, one broken link or dead device can stop the whole loop. **Dual rings** (like the old FDDI standard) send in both directions so traffic can go the other way around a break.

Next, a check on these three shapes.
