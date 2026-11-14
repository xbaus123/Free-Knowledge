# One Click, Part 1: Getting Online

*Wrap-Up · The Whole Course.*

Eleven chapters ago, the Internet was a black box. To finish, let's open it one last time and follow a single click all the way through. You sit down in a café, open your laptop, and go to `https://www.example.org/`. Here's everything that happens in the next second or so, and the chapter that taught you each part.

This half gets you onto the café network and ready to send. Part 2 crosses the Internet.

## 1. Getting on the network

Your laptop hears the café WAP's **beacon**, sends a **probe request**, proves the password with **SAE**, and **associates** (chapter 11). The bits travel as **radio waves**, and the WAP sends them on over **twisted pair** to a switch (chapter 2).

Now at layer 3, a **DHCP** Discover, Offer, Request, Ack hands you an address, a **subnet mask**, a default gateway, and a DNS server (chapters 4 and 5). Your address is **private**, so the café router will **NAT** it on the way out.

## 2. Finding the name

Your laptop knows a name, not an address. It asks its resolver for the **A record** of `www.example.org`. With an empty cache, the resolver asks a **root** server, then a **.org** server, then **example.org's** own authoritative server, over **UDP port 53** (chapter 7).

## 3. The first hop

The answer isn't on your subnet, so the packet goes to the **default gateway**. Your laptop uses **ARP** to learn the gateway's **MAC address** (chapters 3 and 4). The WAP takes the packet out of its **802.11 frame** and puts it in a new **Ethernet frame**, with an **FCS** so any corruption is caught (chapter 3).

Three steps in, and you've already used five chapters. Next, a check on getting online.
