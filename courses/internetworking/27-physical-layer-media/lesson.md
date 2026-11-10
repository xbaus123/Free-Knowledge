# The Physical Layer and Transmission Media

*Chapter 2 · Topologies and the Physical Layer.*

Topology is the shape of a network. The **physical layer**, layer 1, is what the shape is made of. It's the only layer that touches the real world: it turns the bits of a frame into voltages, light pulses, or radio waves, and turns them back into bits at the other end.

Layer 1 doesn't know what a frame, an address, or a packet is. It only knows how to move a `1` or a `0` across a medium, quickly and without losing it.

## The transmission medium

Between the sender's physical layer and the receiver's sits the **transmission medium**: whatever the signal actually travels through.

```
   Sender                                  Receiver
 ┌────────────────┐                    ┌────────────────┐
 │ Physical layer │                    │ Physical layer │
 └───────┬────────┘                    └───────▲────────┘
         │      ┌──────────────────────┐       │
         └─────▶│ Transmission medium  ├───────┘
                │    (cable or air)    │
                └──────────────────────┘
```

## Guided and unguided media

Media come in two families:

- **Guided (wired)** media carry the signal along a physical path. The cable *guides* it from one end to the other.
- **Unguided (wireless)** media send the signal through the air (or space) with nothing guiding it. It spreads out from the antenna and anything in range can pick it up.

```
                         Transmission media
                 ┌────────────────┴────────────────┐
          Guided (wired)                  Unguided (wireless)
     ┌───────────┴───────────┐         ┌───────────┴───────────┐
     │           │           │         │           │           │
  Twisted     Coaxial      Fiber     Radio      Micro-     Infrared
   pair        cable       optic     waves       waves
```

| Family | Medium | Signal | Variants covered in this chapter |
|---|---|---|---|
| Guided | **Twisted pair** | Electrical, on copper wire pairs | Unshielded (UTP), shielded (STP) |
| Guided | **Coaxial cable** | Electrical, on a copper core | Baseband, broadband |
| Guided | **Fiber optic** | Light, through glass or plastic | Single-mode, multimode |
| Unguided | **Radio waves** | Radio, in all directions | |
| Unguided | **Microwaves** | High-frequency radio, aimed in a beam | Terrestrial, satellite |
| Unguided | **Infrared** | Light just below what the eye can see | |

Each medium trades off speed, distance, cost, and how well it resists noise. Before comparing them, you need words for those trade-offs. That's the lesson after the next check.
