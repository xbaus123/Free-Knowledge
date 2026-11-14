# Firmware Resilience

*Chapter 10 · Resilience.*

**Firmware** is the software built into a device: the BIOS or UEFI in a PC, the operating system of a router, switch, or printer, the code in a phone's modem or a smart thermostat. It runs **before** and **underneath** everything else, which makes it a prize target. Malware in firmware survives reinstalling the operating system and even replacing the hard drive.

**Firmware resilience** is the capacity of firmware to resist and recover from failures or attacks while keeping its core functions. It comes from secure firmware, good error handling, redundant and backup copies, and timely updates.

## Robustness

- Firmware **designed with security in mind**, using **secure coding practices**.
- **Code reviews** and **penetration testing** before release.
- **Data privacy**: the firmware shouldn't leak what it handles.
- **Monitoring for vulnerabilities**: watching vendor advisories for every device model you own. Routers, cameras, and printers are easy to forget.

## Resourcefulness

- **Threat design** (threat modeling): thinking through how each device could be attacked, before it is.
- Making **informed decisions**: which devices are critical, which can wait.
- **Incident response plans** that cover firmware, like what to do if a switch's firmware is suspected to be compromised.

## Redundancy

- **Dual firmware**: two copies (often called **A/B** or **dual BIOS**). Update one while the other keeps the known-good version. If the update fails or the device won't boot, it falls back to the other copy.
- **Offline backup** firmware versions, kept where an attacker on the network can't change them.
- Hot and cold sites, and multiple connections, as with hardware.

## Rapidity

- **Firmware restoration**: a tested way to reflash a device to a known-good version.
- **Automated firmware update** systems, so a fix reaches every device in hours, not months.
- **Obtain and verify** patches: download only from the vendor, and check the **digital signature** or **hash** before installing. A fake "update" is a classic way to plant malicious firmware.

## Bricking

An update that fails halfway, like a power cut mid-flash, can leave a device that won't boot at all: **bricked**, about as useful as a brick. Dual firmware and restoration tools are the cure.

Next, a check.
