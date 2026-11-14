# Interference and Coverage

*Chapter 11 · Wireless and IoT.*

Picking channels is half the job. The other half is making sure the signal actually reaches people.

## Frequency reuse

Three non-overlapping channels on 2.4 GHz isn't many, so channels have to be **reused**: WAPs far enough apart that they can't hear each other can use the same channel. A floor plan ends up as a repeating 1, 6, 11 pattern. Cellular networks, in a few readings' time, do exactly the same thing with their towers.

## What blocks the signal

**Keep the area around a WAP open.** Mount it high and in the open, not in a closet or behind a filing cabinet. Some materials are much worse than others. These are rough losses per wall at 2.4 GHz, in decibels (chapter 2's unit of signal loss, where every 3 dB halves the power):

| Obstacle | Rough loss | Why |
|---|---|---|
| Drywall | 3 dB | Light, mostly air |
| Glass window | 4 dB | More if it's coated |
| Brick | 8 dB | Dense |
| **Concrete** | 12 dB | Dense, often with steel bars inside |
| **Metal** (doors, elevators, filing cabinets) | 20 dB or more | Reflects radio almost completely |

**Water** absorbs 2.4 GHz too: fish tanks, and people. A packed room weakens the signal. **Electronic devices** add noise: microwave ovens leak at 2.4 GHz, and Bluetooth, cordless phones, and baby monitors share the band.

## Covering bigger areas

- **Repeaters** (extenders) receive the signal and send it on again. They're easy, but a single-radio repeater has to receive and resend on the same channel, which roughly halves the speed.
- **Mesh** systems use several nodes that coordinate as one network, often with a dedicated radio for the links between them, so clients roam smoothly.
- **Wired backhaul**, an Ethernet cable to each WAP (with PoE from chapter 3), beats both when you can run the cable.

**Keep devices current.** Newer WAPs and clients support faster standards, WPA3, and the 6 GHz band, and firmware updates fix bugs and vulnerabilities (chapter 10).

## Tools

- **Wireshark**, which you may have used for wired captures, can also capture **802.11 frames** when the adapter is in **monitor mode**. You can watch beacons, probe requests, association, and handshakes happen.
- **NetSpot** does **site surveys**: walk the floor plan with a laptop and it draws a **heatmap** of signal strength, and shows which channels nearby networks use.

Next, a check on interference and coverage.
