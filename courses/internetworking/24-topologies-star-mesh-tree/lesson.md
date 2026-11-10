# LAN Topologies: Star, Mesh, and Tree

*Chapter 2 · Topologies and the Physical Layer.*

Point-to-point, bus, and ring are simple shapes. The three in this lesson are what real networks are mostly built from.

## Star

```
   [A]     [B]     [C]
     ╲      │      ╱
      ╲     │     ╱
       ┌─────────┐
       │ hub or  │
       │ switch  │
       └─────────┘
      ╱     │     ╲
     ╱      │      ╲
   [D]     [E]     [F]
```

Every device has its **own cable to a central device**: a hub or, today, a switch.

- **Increased data speed**: each device has a link to itself, so there's no shared backbone to fight over (with a switch, at least).
- Easy to troubleshoot and grow: a bad cable affects only one device, and adding a device means running one more cable to the center.
- **The hub is a single point of failure**: if the central device dies, everyone is cut off.

Almost every office and home network is a star. Your Wi-Fi router is the center of one.

## Mesh

```
   [A] ─────── [B]
    │ ╲       ╱ │
    │   ╲   ╱   │
    │     ╳     │
    │   ╱   ╲   │
    │ ╱       ╲ │
   [D] ─────── [C]
```

Devices connect to **many other devices**, so there are several paths between any two.

- In a **full mesh**, every device links directly to every other one.
- In a **partial mesh**, only some do, usually the most important ones.
- **Reliable data transmission**: if one link fails, traffic takes another path.
- **Redundancy results in additional traffic**: devices have to keep checking all those links and agree on paths, and some data may be sent more than one way. Every extra link is also another cable and port to buy.

A full mesh grows fast. With *n* devices, each one needs *n − 1* links, and the network needs **n × (n − 1) / 2** links in total. Four devices need 6 links. Ten devices need 45. That's why full meshes are kept small, like the core routers of an ISP, while the Internet as a whole is a partial mesh.

## Tree

```
                 [root]
               ╱        ╲
         [switch]      [switch]
         ╱  │  ╲        ╱   ╲
       [A] [B] [C]    [D]   [E]
```

A **tree** (or hierarchical) topology connects several stars to each other in levels, branching from a root down to the devices at the edge.

- **Works well in long-distance and large networks**: a campus can have one star per building, all joined back to a core.
- **Complex to configure** and **increased cost**: more devices, more levels, and more to plan.
- If a branch's link fails, everything below it is cut off from the rest.

Most real networks are **hybrids**: stars joined into a tree, with a partial mesh in the core for redundancy.

## All six at a glance

| Topology | Strength | Weakness |
|---|---|---|
| Point-to-point | Simple, dedicated link | Only connects two devices |
| Bus | Low cost | Hard to troubleshoot, one break kills it |
| Ring | Good quality, no collisions | Limited scalability |
| Star | Fast, easy to manage | Central device is a single point of failure |
| Mesh | Reliable, many paths | Extra traffic and cost |
| Tree | Scales over long distances | Complex to configure, expensive |

Next, a check on star, mesh, and tree.
