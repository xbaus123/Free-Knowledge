# Layer 1 in Practice and Physical Security

*Chapter 2 · Topologies and the Physical Layer.*

On paper the physical layer is voltages and light pulses. In practice it's everything you can touch: cables, closets, rooms, and the building around them. Layer 1 means **dealing with the systems and their environment before anything is ever connected**.

## What "the physical layer" covers in real life

- **Cables**: the right type and category for the job. Wired Ethernet is the **IEEE 802.3** family of standards. (Wi-Fi is **802.11**, the wireless one.)
- **Cabling paths**: where the cables run, how long they are (remember the 100 m limit), and whether they pass near noise sources like elevator motors or power lines.
- **"Is it plugged in?"**: the most common network fix is still physical. Port lights tell you a lot: **green** usually means a good link, **yellow or amber** usually means a problem or a slower speed, and **red** or no light means no link at all. Check the light before you check the configuration.
- **Hubs and other central devices**, and the **end devices**: laptops, desktops, tablets, phones.
- **Servers**, and the room they live in.
- **Building security**, **room security**, and the **room environment**: heating, cooling, power, and humidity. A server room that overheats is down just as surely as one with a cut cable.

## Physical security

If an attacker can walk up to your equipment, they can unplug it, steal it, or plug in their own device. No firewall helps then. Physical security works in layers, from the outside in.

**Around the site:**

- **Video monitoring** (cameras) to deter and record.
- **Exterior lighting**, so nobody can approach unseen.
- **Fences** to control where people can go.
- **Window coverings**, so screens and whiteboards can't be read from outside.

**At the doors:** something checks who you are before it opens:

- **Card readers**: tap or swipe a badge.
- **Touchpads**: enter a PIN.
- **Biometric scanners**: fingerprint, hand, face, or iris.

## Separation

Sensitive systems are kept apart, physically and logically, so one breach doesn't reach everything:

- Separate **networks**: a guest Wi-Fi that can't reach the company's servers.
- Separate **hosts**: the payroll server isn't also the web server.
- Separate **LANs**: different departments or security levels on different local networks.

## The extreme end: SCIFs and Faraday cages

- A **Faraday cage** is an enclosure of conductive metal mesh or sheet that **blocks electromagnetic signals** from getting in or out. Phones inside lose signal, and the signals from equipment inside can't be picked up from outside.
- A **SCIF (Sensitive Compartmented Information Facility)** is a room or building accredited for handling classified information. It combines all of the above: strict access control, alarms, sound-proofing, no personal electronics, and often Faraday-style shielding so nothing can be overheard electronically.

Most networks don't need a SCIF. But every network needs someone to have asked: *who can physically reach this equipment?*

Next, a check on layer 1 in practice and physical security.
