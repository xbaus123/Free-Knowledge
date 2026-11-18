# Peer-to-Peer Computing

*Chapter 1 · Part 7: Computing Environments.*

Client-server draws a firm line: servers serve, clients ask. **Peer-to-peer** (P2P) is **another model of distributed system** that erases that line.

## No clients, no servers: peers

P2P **does not distinguish clients and servers**. Instead, **all nodes are considered peers**, and each **may act as a client, a server, or both**.

```
          client
        /   |   \
  client ───┼─── client        every node can ask, and every node can answer
        \   |   /
     client ─ client
```

## Joining the network

A node **must join the P2P network** before it can take part. Then it finds services in one of two ways:

1. **Central lookup**: when a node joins, it **registers its service with a central lookup service** on the network. A node looking for a service asks the lookup service which peer provides it, then talks to that peer directly.
2. **Discovery protocol**: there's no central lookup. A node that wants a service **broadcasts a request** to the network, and peers that can provide it **respond**. Nodes must also **respond to requests for service** that they can fill.

## Examples

- **Napster**: a music-sharing service that used a **central lookup** server to find which peer had a song, then transferred the file directly between peers.
- **Gnutella**: a file-sharing network with **no central server**: requests were broadcast to peers.
- **Voice over IP (VoIP)**, such as **Skype**, also uses peer-to-peer ideas to connect calls.

| | Client-server | Peer-to-peer |
|---|---|---|
| Roles | Fixed: clients ask, servers serve | Every node is a peer: client, server, or both |
| Finding a service | Ask the known server | Central lookup service, or broadcast with a discovery protocol |
| Examples | A file server, a database server | Napster, Gnutella, Skype |

Next, a check on peer-to-peer computing.
