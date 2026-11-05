# Why Networks Are Built in Layers

*Chapter 1 · Intro to Networks.*

Sending a web page from a server to your laptop involves electrical signals, radio waves, error checking, addresses, routes across a dozen networks, retransmitting lost data, encryption, and HTML. No one could design or debug all of that as one piece. Networks are built in **layers** instead, and the rest of this course works through them one at a time.

## Why layers are important

Each layer does one job, and relies on the layer below it without knowing how that layer works:

- **Each layer focuses on one problem.** The engineer writing a Wi-Fi driver doesn't think about web pages, and the engineer writing a web browser doesn't think about radio.
- **Each layer reads its own part of the packet.** Every layer adds its own **header** to the data. On the receiving side, each layer reads only the header its partner layer wrote, then hands the rest up. A router reads the network header and never looks at the web page inside.
- **Applications don't need to know the path.** A program sends data to an address. Whether it crosses fiber, copper, or a satellite, and through how many routers, is invisible to it.
- **Splitting and rebuilding data is invisible.** The lower layers break a long conversation into packets and put it back together at the other end. The application just sees a stream of data, unless it works at the session layer and manages that itself.
- **Layers can be swapped.** Replace Ethernet with Wi-Fi and nothing above the data link layer changes. That's how the Internet achieves *network technology independence*.

### The catch: tunneling

Because layers only look at their own headers, you can put a whole packet *inside* another packet as if it were ordinary data. That's **tunneling**. It's how VPNs work: your traffic is wrapped in an encrypted outer packet addressed to the VPN server.

Tunneling becomes a big **security issue** because a firewall that inspects the outer headers sees only what the outer packet claims to be. Attackers hide traffic inside protocols that are allowed through: DNS queries, web requests, or ping messages that secretly carry stolen data or remote commands. Keep this in mind whenever a later chapter says "the firewall only looks at the port number."

Next, a short check on layering and tunneling.
