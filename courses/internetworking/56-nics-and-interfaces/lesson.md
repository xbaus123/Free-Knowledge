# Where Layer 2 Lives: The NIC

*Chapter 3 · The Data Link Layer.*

The data link layer isn't an abstract idea floating somewhere in the network. It runs in **every host**, and almost all of it is in one piece of hardware.

## The network interface card

The link layer is implemented in the **network interface card (NIC)**, or in a chip on the motherboard that does the same job. The NIC implements **both layer 2 and layer 1**: it builds frames, and it turns them into signals on the medium.

```
  ┌────────────── host ───────────────┐
  │   ┌─────┐            ┌────────┐   │   application ┐
  │   │ CPU │            │ memory │   │   transport   │ software, on the CPU
  │   └──┬──┘            └───┬────┘   │   network     │
  │ ═════╧═══ host bus (PCIe) ═╧═════ │   link ───────┘
  │        ┌───────┴────────┐         │
  │        │   controller   │  ◀───── │── link       ┐ the NIC
  │        │    physical    │         │   physical    ┘
  │        └───────┬────────┘         │
  └────────────────┼──────────────────┘
                   └── cable or radio
```

- The NIC plugs into the host's **system bus** (PCI or PCIe on a desktop), so the CPU can hand it data.
- A **controller** chip on the NIC does the link layer work. The physical layer part drives the cable or antenna.
- It's a **combination of hardware, software, and firmware**: the controller is hardware, the NIC runs firmware, and the operating system's driver is software.

## Two interfaces talking

When two neighbors exchange a frame, each side does half of the work:

**Sending side**
1. Takes the datagram from the network layer.
2. **Encapsulates** it in a frame: adds the header with addresses and the trailer with error-checking bits.
3. Adds whatever else the protocol offers: reliable delivery, flow control.
4. Hands the bits to the physical layer.

**Receiving side**
1. Takes the bits off the medium and rebuilds the frame.
2. **Checks for errors**, and handles reliable delivery and flow control.
3. **Extracts the datagram** and passes it up to the network layer.

That's encapsulation and de-encapsulation from Chapter 1, at exactly one layer.

## Layer 2 technologies

Plenty of devices work with frames. You'll meet each of these in this chapter:

| Device | Its layer 2 role |
|---|---|
| **NIC** | Builds and receives frames for one host. Holds the host's MAC address |
| **Hub** | Strictly layer 1: repeats every signal out of every port. Listed here because it's what switches replaced |
| **Bridge** | Joins LAN segments and filters frames by MAC address |
| **Switch** | A many-port bridge: forwards each frame only toward its destination |
| **Router** | A layer 3 device, but every router port is a NIC that frames and unframes packets |
| **Wireless access point** | Bridges between radio (802.11) and wired Ethernet |
| **Hypervisor** | Runs virtual machines, with **virtual switches** connecting their virtual NICs |

Next, a check on NICs and how two interfaces exchange a frame.
