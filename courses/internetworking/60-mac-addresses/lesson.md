# MAC Addresses

*Chapter 3 · The Data Link Layer.*

Layer 2 is sometimes called the **MAC layer** (Media Access Control), because this is where a device's **MAC address** lives. Every NIC has one, and it's what Ethernet and WiFi frames use to say who they're from and who they're for. It's foundational: before a host can do anything on a LAN, frames have to reach it by MAC address.

## What one looks like

A MAC address is **48 bits (6 bytes)**, written as 12 hex digits in pairs:

```
   3c : bd : c5 : 40 : 77 : 61
  └──── OUI ─────┘└─ device ID ─┘
   manufacturer     unique to this NIC
```

You'll see the same address written several ways: `3c:bd:c5:40:77:61` (macOS, Linux), `3C-BD-C5-40-77-61` (Windows), or `3cbd.c540.7761` (Cisco). They're all the same 48 bits.

- The **first half (24 bits)** is the **OUI, Organizationally Unique Identifier**. The IEEE assigns each manufacturer one or more OUIs, so the OUI tells you who made the NIC. Online lookups such as macvendors.com, and published OUI lists, map OUIs to vendors.
- The **second half** is a serial number the manufacturer assigns, unique within that OUI.

MAC addresses are "burned in" at the factory, which is why they're also called **hardware** or **physical** addresses. Unlike an IP address, a MAC address doesn't change when the device moves to another network.

## Two special bits

The two lowest bits of the **first byte** have special meanings:

```
  first byte 3c = 0011 11 0 0
                           │ └── bit 0, I/G: 0 = unicast (one NIC), 1 = multicast (a group)
                           └──── bit 1, U/L: 0 = universal (from the OUI), 1 = locally administered
```

- **Multicast**: if the first byte is odd, the frame is for a group. `01:00:5e:...` addresses carry IPv4 multicast.
- **Broadcast**: `ff:ff:ff:ff:ff:ff`, all ones, means *every* device on the LAN. Every NIC accepts it.
- **Locally administered**: if the second hex digit is **2, 6, A, or E**, the address wasn't assigned by a manufacturer: software made it up. Modern phones and laptops do this on purpose: iOS, Android, macOS, and Windows can use a **random (private) MAC address** on each WiFi network so you can't be tracked from network to network. A vendor lookup on one of these finds nothing.

## Finding your MAC address

| System | Where to look |
|---|---|
| **macOS** | System Settings → Network → your network → Details → Hardware. Or `ifconfig en0` in Terminal (the `ether` line) |
| **Windows** | Control Panel → Network and Internet → Network and Sharing Center → your network → Details → **Physical Address**. Or `ipconfig /all` |
| **Linux** | `ifconfig` (listed as `HWaddr` or `ether`) or `ip link` |
| **ChromeOS** | Click the time (bottom right) → Network → your network |

Next, a check on MAC addresses.
