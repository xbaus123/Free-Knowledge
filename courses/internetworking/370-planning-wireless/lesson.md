# Project: Plan Your Wireless and IoT

*Chapter 11 · Wireless and IoT.*

This is the **final piece of the class project**. Chapters 2 to 10 designed your network: rooms and cables, VLANs, subnets, routing, DNS, mail, the website, and resilience. This assignment adds the **wireless and IoT** pieces, and with them your design is complete, from the cables in the walls to the sensors on the ceiling.

**Bring your network drawing to class.** If you're building it in **Cisco Packet Tracer (CPT)**, we'll go around the room and help make sure your segments are correct and operational. If you're not using CPT, we can still review your drawing.

## The questions

**1. Usage.** Which areas are light, medium, or heavy? Count devices at the busiest time, not people.

**2. Access points.** How many WAPs, and where? Coverage should overlap so users roam and a failed WAP is covered. Keep them high and in the open, away from metal, concrete, and the break-room microwave.

**3. Channels.** Which 2.4 GHz channels (1, 6, 11), and where do 5 GHz or 6 GHz serve heavy users?

**4. SSIDs and segments.** One SSID per group that needs separating (staff, guests, IoT), each mapped to its **own VLAN and subnet** from chapters 3 and 5.

**5. Security.** WPA3 everywhere you can (Enterprise for staff), WPA2 only for old devices on their own segment, and chapter 3's WAP hardening: new admin passwords, firmware updates, no remote management.

**6. IoT.** List every IoT device. Change default passwords, keep firmware updated, firewall each segment so devices reach only what they need, and record a **known-good** profile for each sensor.

**7. Other radios.** Any Bluetooth, Zigbee, or LoRa? A **cellular** backup link to the Internet, for chapter 10's redundancy?

**8. Checking it.** Survey with NetSpot after installing, and capture with Wireshark when something looks wrong.

## A worked example

The office from earlier chapters, now with wireless:

| Area | Choice |
|---|---|
| Usage | Offices medium (video calls); conference room heavy at meeting times; lobby light |
| Access points | Six ceiling-mounted WAPs on PoE with wired backhaul, coverage overlapping about 20% |
| Channels | 2.4 GHz on 1, 6, 11, 1, 6, 11; 5 GHz at 80 MHz in offices; 6 GHz in the conference room |
| SSIDs | `Staff` to VLAN 10 (WPA3-Enterprise), `Guest` to VLAN 30 (WPA3-Personal, internet only), `Devices` to a new **VLAN 50** on 10.1.50.0/24 for IoT (WPA3, or WPA2 for the old printer) |
| Cameras | Stay wired on VLAN 40, no internet, reachable only from the recorder |
| IoT rules | VLAN 50 reaches only the building controller and vendor update servers; default passwords changed on arrival; known-good profiles alert on new destinations |
| Other radios | A Zigbee hub for lights on a channel between Wi-Fi 6 and 11; an LTE router as a backup internet link |
| Checking | NetSpot survey after install and once a year; Wireshark for troubleshooting |

When you're done, step back and look at the whole drawing. Every box and line on it is something you can now explain, layer by layer.

Next, a check on planning your wireless and IoT.
