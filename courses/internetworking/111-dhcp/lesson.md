# DHCP: Getting an Address Automatically

*Chapter 4 · The Network Layer.*

When your laptop joins a WiFi network, nobody types in an address for it. It gets one **dynamically**, from a server on the network, using the **Dynamic Host Configuration Protocol (DHCP)**.

## Why dynamic?

- **Reuse**: a host only holds an address while it's connected. A coffee shop with 50 seats can serve thousands of customers a week from a pool of 100 addresses.
- **Mobility**: users join and leave all the time, and get a working address wherever they go.
- **No typing**: along with the address, DHCP hands out the **subnet mask**, the **default gateway**, and the **DNS servers**. One mistyped gateway can't break anyone's network.

## The four messages: DORA

A new host has no address yet, and doesn't know where the server is. So it **broadcasts**:

```
  client (no address yet)                          DHCP server
        │ ── 1. DISCOVER (broadcast) ─────────────────▶ │  "Is there a DHCP server?"
        │ ◀─────────────────────── 2. OFFER ─────────── │  "You can have 10.104.216.118"
        │ ── 3. REQUEST (broadcast) ──────────────────▶ │  "I'll take 10.104.216.118"
        │ ◀────────────────────────── 4. ACK ────────── │  "It's yours for 8 hours"
```

1. **Discover**: the host broadcasts, from source 0.0.0.0 to **255.255.255.255**, asking for any DHCP server.
2. **Offer**: a server offers an address (plus mask, gateway, DNS).
3. **Request**: the host asks for that address. It's broadcast too, so any *other* servers that made offers know they weren't picked.
4. **Ack**: the server confirms. The host can now use the address.

**D**iscover, **O**ffer, **R**equest, **A**ck: **DORA**. DHCP runs over **UDP**: servers listen on port **67**, clients on port **68**.

The first two steps are **optional**: a host that remembers the address it had last time can skip straight to a Request for it.

## Leases

An address is given out on a **lease**, for a set time (an hour, a day, a week). Halfway through, the host asks to **renew** it, and normally keeps the same address. If the host leaves without saying goodbye, the lease simply runs out, and the address goes back into the pool.

On Windows, `ipconfig /release` gives the address back and `ipconfig /renew` runs DHCP again, a classic first step when a network connection misbehaves. And recall: a host that gets **no answer** gives itself a **169.254.x.x** address.

## Security

DHCP has no authentication, like ARP. A **rogue DHCP server** (a misconfigured home router plugged into an office network, or an attacker) can hand out its own address as the gateway and DNS server, and see everyone's traffic. Managed switches defend against it with **DHCP snooping**: only ports you trust may send Offers and Acks.

Next, a check on DHCP.
