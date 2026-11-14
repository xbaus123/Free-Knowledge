# Wireless vs Wired

*Chapter 11 · Wireless and IoT.*

Welcome to the **last chapter** of the course. Chapters 2 to 10 built the stack from the cables up, and nearly all of it ran on wires. This chapter cuts them. It covers Wi-Fi, cellular, and the low-power radios behind the **Internet of Things (IoT)**: the sensors, cameras, locks, and light bulbs that are now on most networks.

Wireless is a fitting place to finish, because it touches almost everything you've learned: radio is the physical layer, access points are layer 2, DHCP hands out addresses, and resilience and security decide whether any of it can be trusted. Watch for the callbacks.

## Wi-Fi is radio

Chapter 2 introduced radio waves, and Wi-Fi is just that. Every Wi-Fi device is a **two-way radio** that both transmits and receives. Nothing physically joins your laptop to the network. You're connected, but not really: you're sharing the air with every other radio in range.

Cell phones, Bluetooth headphones, and IoT sensors work the same way, on different frequencies and at different power levels. Wi-Fi uses two main bands:

| Band | Strengths | Weaknesses |
|---|---|---|
| **2.4 GHz** | Longer range, gets through walls better | Few channels, and crowded: microwave ovens, Bluetooth, and Zigbee all share it |
| **5 GHz** | Faster, with many more channels | Shorter range, blocked more easily |

Newer equipment adds a third band at **6 GHz**, which comes up again in the planning reading.

## How Wi-Fi differs from wired

| | Wired | Wireless |
|---|---|---|
| **Physically** | Signals inside a cable | Signals through the air |
| **Speed** | Faster | Slower, and shared by everyone on the channel |
| **Reliability** | Stable, with guaranteed speed and performance | Prone to interference, so speed varies |
| **Security** | Better. An attacker needs the cable, and **forensics** is easier because every cable runs to a known switch port | Needs encryption. The airwaves are free for anyone to listen to, and even encrypted traffic shows **patterns**: who's talking, when, and how much |
| **Mobility** | Stuck where the jack is | Move anywhere in range |
| **Maintenance** | Expensive up front (pulling cable through walls), cheap over time | Cheap to install, but needs ongoing tuning and newer equipment |

## Which goes where

- **Wired** wins where **security, throughput, and availability** matter most: data centers, server rooms, the links between switches, and anything doing heavy processing.
- **Wireless** wins where **flexibility** matters: laptops and phones, meeting rooms, warehouses, temporary sites, and sensors in places a cable can't reach.

Most real networks are both: a **wired core** with **wireless at the edge**, joined by the access points you met in chapter 3.

Next, a check on wireless versus wired.
