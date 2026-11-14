# Planning Wi-Fi: Usage and Channels

*Chapter 11 · Wireless and IoT.*

A Wi-Fi network that works in an empty office can fall over at the all-hands meeting. Planning starts with two questions: **how much will people use it**, and **which channels will each access point use**?

## Determine usage

| Usage | Bandwidth | Typical use |
|---|---|---|
| **Light** | 5 to 25 Mbps | Browsing, social media, email, a small number of devices |
| **Medium** | 50 to 300 Mbps | Video calls, multiple users |
| **Heavy** | 500+ Mbps | Gaming, heavy streaming, HD video, multiple users |

Plan for the **busiest** time, not the average, and count devices, not people: most people carry a laptop and a phone, and both are on the Wi-Fi.

## Channel planning on 2.4 GHz

The 2.4 GHz band is cut into channels numbered 1 to 13 (1 to 11 in North America). Their centers are only **5 MHz apart**, but each signal is about **22 MHz wide**, so neighboring channels overlap and interfere. Only **1, 6, and 11** stay clear of each other:

```
 channel:  1    2    3    4    5    6    7    8    9   10   11
           [=======1=======]
                               [=======6=======]
                                                   [=======11======]
```

Access points near each other should use **different** non-overlapping channels: 1, 6, 11, 1, 6, 11 across the floor.

## Faster bands

- **5 GHz** has many more non-overlapping channels, and they can be **bonded** into wider 40, 80, or 160 MHz channels. More MHz means more speed, so plan the wide channels where high speed is needed.
- **6 GHz** (Wi-Fi 6E and Wi-Fi 7) opens a whole new band that older devices can't use, so it's far **less saturated**. Moving heavy users from 5 GHz up to 6 GHz frees space for everyone else. (These are radio bands, not the "5G" and "6G" of cell phone generations.)

## Overlapping access points

Coverage areas should **overlap**, even though channels shouldn't. Overlap means a walking user roams to the next WAP before the signal drops, and if one WAP fails, its neighbors still cover the area. That's chapter 10's **redundancy**, applied to radio.

Next, a check on usage and channel planning.
