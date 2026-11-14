# Joining a Wi-Fi Network

*Chapter 11 · Wireless and IoT.*

What actually happens between opening your laptop and loading a web page over Wi-Fi?

## The pieces

- A **wireless access point (WAP)** is a **layer 2** device (chapter 3). It bridges the radio side onto the wired LAN, and its **antennas** send and receive the radio signal.
- A WAP alone doesn't reach the Internet. It needs a **router**, and the router needs a **modem** to convert between Ethernet and whatever the ISP's line carries (cable, DSL, or fiber).

At home, one box usually does it all: antennas, WAP, switch, router, and often the modem. That's what people call a "wireless router."

## Beacons and SSIDs

A WAP announces itself by broadcasting **beacon** frames, about **10 times a second**. Each beacon carries the **SSID** (**Service Set Identifier**), the network's name, plus what security and speeds it supports.

When your laptop shows a list of available networks (Lenovo Smart Clock, ARRIS-C665, a printer's `DIRECT-` network, and so on), that list is simply the **beacons it has heard**. The lock icon means the network wants credentials.

## Step by step

1. **Listen.** 802.11 devices share the channel with **CSMA/CA** (chapter 3): listen first, and wait a random time before sending. Just listening for beacons is called **passive scanning**.
2. **Probe.** For **active scanning**, the client broadcasts a **probe request** ("who's out there?", or "is *CoffeeShop* here?"), and each WAP answers with a **probe response** carrying its SSID.
3. **Authenticate.** The client proves it knows the shared secret. On an open network, no credentials are needed at all.
4. **Associate.** The client sends an **association request**, and the WAP's **association response** connects the two devices. They're now linked at **layer 2**.
5. **Get an address.** Only now can the client ask the **DHCP** server (chapter 4) for an **IP address**, gateway, and DNS server. That's layer 3.
6. **Keep probing.** The client keeps sending probes now and then. If it moves and finds a stronger WAP for the same network, it **roams** to it. That's what keeps a phone connected as you walk down a hallway.

```
 Client                                   WAP
   |  <-------------- beacon (SSID) -------- |   passive scan
   |  ---- probe request ------------------> |   active scan
   |  <-------------- probe response ------- |
   |  ---- authentication -----------------> |
   |  <------------------------------------- |
   |  ---- association request ------------> |
   |  <-------------- association response - |   layer 2 link up
   |  ==== DHCP for an IP address ========== |   layer 3
```

With WPA2, the password is really checked just after association, in a **4-way handshake**. WPA3 checks it during authentication. That's the next reading.

Next, a check on joining a Wi-Fi network.
