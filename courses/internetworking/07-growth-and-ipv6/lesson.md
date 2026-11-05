# Growth, Its Problems, and IPv6

*Chapter 1 · Intro to Networks.*

The Internet's designers built it for a few hundred research computers. This lesson is about what happened when it grew to hundreds of millions, and the protocol designed to cope.

## Growth, and the problems it brought

The Internet had about 200 computers in 1981. By 2011 it had over 800 million. On a linear chart that growth looks like nothing at all until the mid-1990s, then a hockey stick. On a **log scale**, where each step up the axis is ten times more, it looks like a nearly straight line: the number of hosts multiplied by about ten every few years for decades, and only began to flatten after 2000.

Growth that fast created problems that no one designed for:

- **Unintended use.** TCP/IP was built for researchers sharing computers. Now it carries banking, video, phone calls, and power-grid control, with requirements its designers never imagined.
- **Legacy systems.** Once millions of devices speak a protocol, you can't change it. Old equipment and software stay in service for decades, and every new design has to work with them.
- **Address space.** IPv4 addresses are 32 bits, about 4.3 billion in all. That seemed endless in 1981. The global pool ran out in 2011.
- **Hackers.** The early Internet assumed every host was run by a trusted researcher. Protocols like email and DNS were built with no authentication, and security has been added on top ever since.

## A few words about IPv6

**IPv6** was designed in the 1990s to replace IPv4. Decades later, the two still run side by side: most devices and networks support both. What IPv6 changes:

- **A much larger address space.** Addresses are 128 bits instead of 32, enough to give every device its own public address.
- **An extended address hierarchy.** The extra bits leave room for more levels of structure, so big networks can be split up and routes summarized more neatly.
- **Multicast instead of broadcast.** IPv6 has no broadcast at all. Instead of shouting to every host on a network, a sender addresses a **multicast** group of just the hosts that care. (More on broadcast in the data link chapter.)
- **DNS dependent.** Nobody remembers an address like `2001:db8:85a3::8a2e:370:7334`, so IPv6 relies on DNS names even more than IPv4 does.
- **A new header format.** A simpler fixed-size header that routers can process faster (more on this in the network layer chapter).
- **Improved options and protocol extensions.** Optional features go in separate *extension headers* chained after the main header, so routers can skip what they don't need, and new features can be added later.
- **Autoconfiguration and renumbering.** A host can build its own address from the network's prefix, with no server required, and a whole network can move to a new prefix more easily.
- **Resource allocation.** A *flow label* field lets a sender mark packets that belong to one stream, such as a video call, so routers can give them consistent treatment.

## Further reading

- Douglas Comer, *Internetworking with TCP/IP, Volume One*, chapter 1.
- Craig Hunt, *TCP/IP Network Administration*, chapter 1.

Next, a short check on growth and IPv6, then a timeline drill on everything in the history half of this chapter.
