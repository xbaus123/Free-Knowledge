# Access Points and Hypervisors

*Chapter 3 · The Data Link Layer.*

Two more layer 2 technologies finish the chapter: wireless access points, which bridge radio onto the wired LAN, and hypervisors, which build whole switched networks in software.

## Wireless access points

A **wireless access point (WAP)** is a bridge between 802.11 WiFi and wired Ethernet. Laptops and phones associate with it by radio, and it forwards their frames onto the switch it's plugged into.

Many WAPs are mounted on ceilings, far from a power outlet, so they're powered by **Power over Ethernet (PoE)**: the switch sends electricity down the same Ethernet cable that carries the data. One cable does both jobs.

A WAP is also a way into your network for anyone in radio range, even outside the building. Hardening it:

| Step | Why |
|---|---|
| **Change default settings** | Default admin passwords and network names are published online. Change both |
| **Enable encryption: WPA3** (WPA2 at the very least) | Without it, anyone nearby can read every frame. Never use WEP, which can be cracked in minutes |
| **Update the firmware** | Fixes for known vulnerabilities arrive as firmware updates |
| **Disable remote management** | Only allow admin access from the wired, internal network |
| **Create a guest network** for external users | Visitors get internet access on a separate network that can't reach internal machines |
| **Hide the SSID** | Stops the network name being advertised. A weak measure: the name still appears in devices' connection requests and is easy to sniff |
| **Enable the firewall**, if available | Filters traffic between wireless clients and the rest of the network |
| **Apply MAC filtering rules** | One more layer. As you saw, a MAC address can be cloned, so never the only one |

## Hypervisors

A **hypervisor** runs many virtual machines on one physical server. Each VM has **virtual NICs** with their own MAC addresses, connected to a **virtual switch** inside the hypervisor. Frames between two VMs on the same host never touch a physical wire. That's layer 2 entirely in software, and it's what cloud data centers are built on.

Hypervisor features, and what they mean for designing a network that's secure by design:

- **Traffic shaping**: limit how much bandwidth each VM's virtual NIC may use, so one busy or compromised VM can't starve the others.
- **Memory ballooning**: the hypervisor reclaims memory a VM isn't using (a "balloon" driver inside the guest inflates to take it) and lends it to other VMs. Efficient, but VMs share physical resources, so isolation between them matters.
- **Role Based Access Control (RBAC)**, also called authorizations: give each administrator only the rights they need. Whoever controls the hypervisor controls every VM and virtual switch on it.
- **Log and audit**: record who changed what, and when, and review it.
- **Configure multiple processors**: assign virtual CPUs to each VM to match its workload.
- **Cloud computing**: public clouds are hypervisors at enormous scale, with virtual networks (VPCs, virtual switches, and VLAN-like segments) configured in software rather than cabled by hand.

Next, a check on access points and hypervisors.
