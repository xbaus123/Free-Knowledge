# Coaxial Cable: Baseband and Broadband

*Chapter 2 · Topologies and the Physical Layer.*

**Coaxial cable** ("coax") is the round cable that screws into the back of a cable modem or TV. Its name comes from its shape: all of its layers share one axis, nested inside each other.

## Inside a coax cable

```
  ┌──────────────────────────────────────┐  4. outer plastic jacket
  │ ┌──────────────────────────────────┐ │  3. metal shield (braid or foil)
  │ │ ┌──────────────────────────────┐ │ │  2. insulating material
  │ │ │ ════════════════════════════ │ │ │  1. inner conductor
  │ │ └──────────────────────────────┘ │ │
  │ └──────────────────────────────────┘ │
  └──────────────────────────────────────┘
```

From the center out:

1. **Inner conductor**: copper or aluminum. This is where the signal travels.
2. **Insulating material**: usually **polyethylene**, chosen for low signal loss, water resistance, sturdiness, and low cost. It keeps the conductor centered and apart from the shield.
3. **Metal shield**: a braid or foil that **blocks outside noise** from reaching the signal and **keeps the signal inside** from leaking out.
4. **Protective plastic jacket**: protects against physical damage, moisture, dust, dirt, chemicals, heat, and short circuits, and **protects people from electric shock**.

The shield is what makes coax resist interference much better than plain wire.

## Baseband coax

**Baseband** coax carries **a single digital signal** over a **short distance**.

- **No modulation**: the data goes onto the wire directly, as voltage levels, without being shifted onto a carrier frequency. Simple, but less efficient.
- The data is represented as **digital signals**, not analog waves.
- Since there's only one channel, devices share it by taking turns. That's **time-division multiplexing (TDM)**: each device gets its own slice of time.
- **Limited bandwidth**: one channel, no frequency multiplexing, no modulation.
- **Simple**, and used **inside a building's LAN**. Early Ethernet (10BASE2 and 10BASE5, the *BASE* is for baseband) ran on baseband coax in a bus.

## Broadband coax

**Broadband** coax carries **many signals at once** over **long distances**.

- **Relies on modulation**: each signal is put onto its own carrier frequency.
- The data is represented as **analog waves**.
- The cable's frequency range is divided into separate channels, so many signals travel at once with no idle gaps. That's **frequency-division multiplexing (FDM)**, like radio stations sharing the air on different frequencies.
- Used for **long-distance connections** like **cable Internet access** and **cable TV**. TV channels and your Internet traffic share one cable, each on its own frequencies.

TDM and FDM come back in more detail in a later chapter.

## Baseband vs broadband

| | Baseband | Broadband |
|---|---|---|
| Signals at once | One | Many |
| Distance | Short | Long |
| Signal form | Digital | Analog waves |
| Modulation | None | Yes, onto carrier frequencies |
| How the medium is shared | Time slices (TDM) | Frequency channels (FDM) |
| Typical use | A LAN inside a building | Cable Internet and cable TV |

One way to remember it: **base**band is the **basic** one, one signal straight on the wire. **Broad**band uses a **broad** range of frequencies.

Next, a check on coax.
