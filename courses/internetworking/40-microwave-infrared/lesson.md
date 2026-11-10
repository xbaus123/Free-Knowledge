# Microwaves and Infrared

*Chapter 2 · Topologies and the Physical Layer.*

Radio waves spread out in every direction. As the frequency goes up, signals start acting more like beams of light: they travel in straight lines and get stopped by whatever is in the way. Microwaves and infrared are the two high-frequency wireless media.

## Microwaves

**Microwaves** transmit at high frequencies, from **1 GHz to 300 GHz**, with the most common range for communication being **3 to 30 GHz**.

- **Unidirectional**: the signal is focused into a narrow beam aimed from one antenna at another.
- **Line of sight**: the two antennas must be able to "see" each other. To cover longer distances over the curve of the Earth, the antennas go on tall towers, and bigger dish antennas focus the beam more tightly.

There are **two types**:

- **Terrestrial**: dish antennas on towers or rooftops, a few dozen kilometers apart, relaying signals across land. Phone companies and TV stations use them to link sites without laying cable.
- **Satellite**: a dish on the ground aims up at a satellite, which relays the signal back down to a distant point. Satellite TV and satellite Internet work this way.

```
   Terrestrial:   [tower] ─────── beam ───────▶ [tower]

   Satellite:              [satellite]
                          ╱           ╲
                    [dish]             [dish]
```

| Advantages | Disadvantages |
|---|---|
| High-speed data transfer | Physical obstacles can interrupt the beam |
| Easy to install and use | Security risks: the beam can be intercepted |
| Cheap compared to laying cable over the same distance | Limited range per hop |
| Reliable | Atmospheric conditions (heavy rain, fog) can hurt signal quality |
| Fast deployment | |

## Infrared

**Infrared** (IR) is light just below what the human eye can see: roughly **300 GHz to 400 THz**. It's used for **short-range communication**.

- Requires a **transceiver** (a device that can both transmit and receive) on each side.
- **Low cost** and **low power consumption**.
- **High-speed data transfer, but it requires line of sight**: IR can't pass through walls, or even a hand in the way.
- **Limited range**: a few meters.
- **High attenuation**: the signal fades quickly with distance.
- Best used for **remote controls** and **scanning**, like barcode scanners and some contactless sensors.

IR's short range is also a security advantage: a signal that can't leave the room is hard to eavesdrop on.

## The three wireless media together

| | Radio waves | Microwaves | Infrared |
|---|---|---|---|
| Frequency | 3 kHz – 300 GHz | 1 – 300 GHz (usually 3 – 30) | 300 GHz – 400 THz |
| Direction | All directions | Narrow beam | Line of sight |
| Through walls | Yes | No | No |
| Range | Long | Long, with towers or satellites | A few meters |
| Typical use | Wi-Fi, cellular, broadcast radio | Tower-to-tower links, satellite | TV remotes, scanners |

Next, a check on microwaves and infrared.
