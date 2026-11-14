# One Click, Part 2: Across the Internet

*Wrap-Up · The Whole Course.*

Your packet has left the café. Here's the rest of its trip, and what happens after the page loads.

## 4. Across the Internet

Every router does a **longest prefix match** on the destination address, decrements the **TTL**, and forwards the packet on (chapters 4 and 6). Your ISP's routers learned the way to example.org's network through **BGP**, from one **autonomous system** to the next (chapter 6). Run `traceroute` and you'd see every hop.

## 5. The conversation

Your laptop opens a **TCP** connection to port **443**: SYN, SYN/ACK, ACK (chapter 4). **TLS** encrypts the session, the presentation layer's job (chapter 9). Then an **HTTP GET**, and back comes **200 OK** with the page, and a **cookie** so the site remembers you (chapter 9).

On the way down your laptop's stack, each layer wrapped the data in its own header: segment, packet, frame, bits. Every router and switch unwrapped only as far as it needed. That's **encapsulation**, from chapter 1, and it's happening in every step above.

## 6. What happens after

You order something. The shop's mail server looks up your domain's **MX** record and delivers a receipt over **SMTP**, with **SPF**, **DKIM**, and **DMARC** vouching that it's genuine (chapter 8). Behind the scenes, two web servers, **RAID**, and tested backups mean that one dead disk doesn't stop the shop (chapter 10).

## Every chapter, in one click

| Chapter | Its part in the click |
|---|---|
| 1 · Intro to Networks | Packet switching, layers, and encapsulation |
| 2 · Physical Layer | Radio waves and twisted pair carry the bits |
| 3 · Data Link | Frames, MAC addresses, ARP, switches, the WAP |
| 4 · Network Layer | IP, DHCP, NAT, TTL, the TCP handshake |
| 5 · Subnetting | The mask that says "this address isn't local" |
| 6 · Routing | Longest prefix match and BGP across the Internet |
| 7 · DNS | Turning the name into an address |
| 8 · Mail | The receipt in your inbox |
| 9 · Upper Layers | TLS, HTTP, and cookies |
| 10 · Resilience | Why the site is still up when a disk dies |
| 11 · Wireless and IoT | Joining the café Wi-Fi |

All of that, in about a second, billions of times a day, with no central hub in charge.

Next, a check on the rest of the journey.
