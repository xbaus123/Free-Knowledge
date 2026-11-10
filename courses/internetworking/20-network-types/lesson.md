# Network Types: Client-Server and Peer-to-Peer

*Chapter 2 · Topologies and the Physical Layer.*

Chapter 1 covered what the layers do. This chapter starts at the bottom of the stack: how machines are arranged, and what physically carries their bits. First, though, a question that comes before any cable is pulled: **who serves whom?**

## Client-server

In a **client-server** network, one machine (or a group of them) is the **server**. It holds the shared resources and answers requests. Everyone else is a **client**: clients ask, the server answers.

```
            ┌──────────┐
            │  Server  │   files, email, logins, web pages
            └────┬─────┘
       ┌─────────┼─────────┐
   ┌───┴───┐ ┌───┴───┐ ┌───┴───┐
   │Client │ │Client │ │Client │
   └───────┘ └───────┘ └───────┘
```

- The **central server provides the services**: file storage, email, authentication, printing, the web.
- It **manages traffic**: it decides who's allowed in, what they can see, and how requests get handled.
- One place to back up, patch, and secure.
- The catch: if the server goes down, every client loses the service. The server is a **single point of failure** unless you add more servers.

"Server" is a **role**, not a kind of hardware. A laptop running a web server is a server for as long as it answers requests.

## Peer-to-peer

In a **peer-to-peer (P2P)** network there is **no central server**. Every host is a **peer**, and **each host is responsible for sharing its own resources and data**. Any peer can be a client one moment and a server the next.

```
   Peer ────────── Peer
    │ ╲           ╱ │
    │   ╲       ╱   │
    │     ╲   ╱     │
    │       ╳       │
    │     ╱   ╲     │
    │   ╱       ╲   │
    │ ╱           ╲ │
   Peer ────────── Peer
```

- Cheap and simple to set up: no dedicated server to buy or run.
- No single point of failure: one peer leaving doesn't take the others down.
- **Size constrained**: with no central control, every peer manages its own sharing and security. That works for a handful of machines, but at 50 machines nobody knows who has what or who's allowed to see it.

## Side by side

| | Client-server | Peer-to-peer |
|---|---|---|
| Central server | Yes | No |
| Who shares resources | The server | Every host |
| Control and security | Centralized, one place to manage | Spread out, each host manages its own |
| Cost to start | Higher (server hardware, admin) | Low |
| Scales to | Thousands of users | A small group |
| Server fails | Everyone loses the service | Only that peer's resources go away |
| Example | A company file server, a website | A home network sharing a printer, file-sharing apps |

Many real systems are **hybrids**. A file-sharing app may use a central server just to help peers find each other, and then move the data directly between peers.

Next, a quick check on client-server and peer-to-peer.
