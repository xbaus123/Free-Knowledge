# The Session Layer

*Chapter 9 · Upper Layers.*

A **session** is a conversation between two devices that lasts longer than one message. TCP gives you a reliable byte stream, but it doesn't know that the bytes belong to "Alice's login", "this game match", or "this phone call". The session layer does.

## What the session layer does

| Job | What it means |
|---|---|
| **Establish** | Set up the conversation: who's talking, with what settings |
| **Maintain** | Keep it going, decide who talks when (**dialogue control**) |
| **Synchronize** | Keep streams lined up and mark recovery points |
| **Terminate** | End it cleanly, so both sides free their resources |

## Sessions you already use

- **Logging in.** You prove who you are once, and the server remembers you for the rest of the session, so you don't type your password on every click. Log out, or sit idle too long, and the session ends.
- **Multi-player gaming.** Joining a match sets up a session, the game keeps every player's state in step, and leaving or disconnecting tears it down.
- **Database sessions.** An application connects to a database, logs in, runs many queries, and disconnects.
- **RPC** (remote procedure calls): a program calls a function that actually runs on another machine.
- **SIP**: setting up voice and video calls.

## Session vs connection

A session is **not** the same as a TCP connection:

- One session can use **many** connections. A web login survives you closing the tab and opening a new one, even though each page load may use a fresh TCP connection.
- One connection can carry **many** sessions. A database connection pool hands the same TCP connection to different users one after another.

Next, a check on what sessions are.
