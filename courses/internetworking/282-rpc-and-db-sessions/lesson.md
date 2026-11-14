# RPC and Database Sessions

*Chapter 9 · Upper Layers.*

Two more session-layer examples from the slides, both common inside data centers.

## RPC: remote procedure calls

An **RPC** lets a program call a function that **runs on another machine**, as if it were a local call:

```python
total = inventory.count_items("widget")   # actually runs on the inventory server
```

Behind that one line:

1. A **client stub** packs the function name and arguments into a message (this packing is called **marshalling**, and it's presentation-layer work).
2. The message goes to the server over the network.
3. A **server stub** unpacks it, calls the real function, and packs up the result.
4. The result comes back, and the caller carries on.

The session part is keeping track of **which reply belongs to which call**, what to do if the server doesn't answer, and when the conversation is over. Examples: **gRPC** (common between microservices), **Microsoft RPC** (port **135**), and the RPC system **NFS** file sharing is built on.

## Database sessions

When an application talks to a database, it opens a session:

1. **Connect and log in**: the database checks the user and creates a session for it.
2. **Run queries.** The session remembers things between them: the current database, settings, and any open **transaction**.
3. **Transactions**: `BEGIN`, several changes, then `COMMIT` (keep them all) or `ROLLBACK` (undo them all). The commit is a **checkpoint**: after a crash, the database recovers to the last committed state.
4. **Disconnect**, or the session **times out** if it sits idle.

Opening a session costs time (TCP handshake, TLS, login), so busy applications keep a **connection pool**: a set of open sessions reused again and again.

Next, a check on RPC and database sessions.
