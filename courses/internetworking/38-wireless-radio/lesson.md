# Wireless Media and Radio Waves

*Chapter 2 · Topologies and the Physical Layer.*

Unguided media send signals through the air, with no cable to guide them. There are **three types of wireless transmission**, and they differ mostly in **frequency**: how many times per second the wave oscillates, measured in hertz (Hz).

```
 lower frequency ─────────────────────────────────────────▶ higher frequency

 3 kHz                    1 GHz              300 GHz             400 THz
   │◀────────────── radio waves ───────────────▶│
                            │◀── microwaves ───▶│◀─── infrared ────▶│
```

Microwaves are really the high end of the radio range, but they behave differently enough to get their own name. As a rule of thumb, **the higher the frequency, the more data it can carry, but the shorter its range and the more easily it's blocked.**

## Radio waves

**Radio** communication uses a **transmitter**, a **receiver**, and an **antenna** on each, across roughly **3 kHz to 300 GHz**. Lower-frequency radio waves spread out in every direction and pass through walls, which is why your Wi-Fi works in the next room and an AM station reaches across a state.

**Pros:**

- **Long-distance communication**, since low frequencies travel far and bend around obstacles.
- **Portable**: no cable, so devices can move.
- **Reliable**, and **easily installed**: put up an antenna and you're done.

**Cons:**

- **Prone to interference**: every other transmitter on a nearby frequency is noise.
- **Atmospheric disturbances**, like storms and solar activity, can disrupt the signal.
- **Limited bandwidth**: the radio spectrum is shared by everyone in the area, and governments license out slices of it.
- **Health concerns** are often raised. Radio waves are *non-ionizing*, and normal exposure isn't considered harmful, but limits on transmitter power exist for safety.

Wi-Fi, Bluetooth, cellular phones, and broadcast radio all use radio waves.

## Why is wireless inherently less secure?

A cable keeps its signal inside a jacket. To listen in, an attacker has to physically get at the cable. A radio signal **spreads out in every direction**, through walls and into the parking lot, and **anyone within range** with a receiver can pick it up. Nobody has to break into the building.

That means:

- **Eavesdropping** is passive and invisible: you can't tell who's listening.
- Attackers can **pretend to be your network**, setting up a fake access point with the same name.
- Attackers can **jam** the frequency with noise.

This is why wireless networks lean so heavily on **encryption** (like WPA3 for Wi-Fi). On a wired network, the building walls are the first line of defense. On a wireless one, encryption is.

Next, a check on wireless basics and radio waves.
