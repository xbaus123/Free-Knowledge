# MAC Address Security

*Chapter 3 · The Data Link Layer.*

Because the MAC address is burned in at the factory, it's tempting to treat it as a fingerprint: "only let these MAC addresses onto the network." Plenty of networks do. But a MAC address is a weak way to identify anything, for three reasons.

## Spoofing

The burned-in address is only the *default*. Every major operating system lets you set the address a NIC actually uses, in a single command or settings field. **MAC spoofing** means sending frames with a source MAC address that isn't yours. An attacker might spoof to:

- get past **MAC filtering** (an allow list of permitted addresses),
- hide which device they're using, or
- pose as another machine to intercept its traffic.

There's nothing in an Ethernet frame that proves the source address is true. Switches and access points simply believe it.

## Cloning

**MAC cloning** is spoofing with a specific target: copying the exact MAC address of a device that the network already trusts. Run a packet sniffer on a WiFi network, note the MAC address of a laptop that's allowed on, wait for it to leave, and use that address.

Cloning has a legitimate use too. Some ISPs lock service to the MAC address of the first device you connect, so home routers have a "clone MAC address" setting that copies your old computer's address to the router's WAN port.

## One address, many users

Even when a MAC address is genuine, it identifies a **NIC, not a person**:

- A shared family computer, a lab PC, or a kiosk is used by many people under one MAC address.
- One person has several devices, each with its own MAC addresses (WiFi and Ethernet are separate NICs).
- Random private addresses (from the last lesson) mean the same phone shows up as a different MAC on different networks, and some devices rotate it over time.

So logs that say "MAC aa:bb:... did this" don't tell you *who* did it.

## What this means

MAC filtering is worth turning on as **one layer of defense**: it stops casual connections. But it must never be the only protection. Real access control needs authentication (passwords, certificates, 802.1X logins) and encryption, which we'll come back to with wireless access points.

Next, a check on MAC address security.
