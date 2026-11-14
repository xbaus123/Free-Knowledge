# Dialogue Control: Who Talks When

*Chapter 9 · Upper Layers.*

Once a session is up, the two sides need rules about **who may send, and when**. That's dialogue control, and there are three modes.

## Simplex

**One direction only.** One side sends, the other only listens.

- Examples: broadcast radio and TV, a display board showing departure times, a sensor that only reports.
- **Cheap**: one path, and the receiver needs no transmitter.
- **No transmission guarantee**: the receiver can't send back "got it" or "say again", so the sender never knows whether anything arrived.

## Half duplex

**Both directions, but not at the same time.** The sides take turns.

- Examples: walkie-talkies ("over"), and chapter 3's Ethernet **hubs**, where only one device on the shared wire can transmit at once.
- One path is enough, but time is wasted handing over the turn, and if both talk at once you get a **collision**.

## Full duplex

**Both directions at the same time.**

- Examples: a phone call, switched Ethernet, a video call where you can interrupt each other.
- It needs **two paths per device**, one to **transmit** and one to **receive**: separate wire pairs in twisted pair, two strands of fiber, or two radio channels.

| Mode | Directions | At the same time? | Paths | Example |
|---|---|---|---|---|
| **Simplex** | One | n/a | 1 | Broadcast radio |
| **Half duplex** | Two | **No**, take turns | 1 | Walkie-talkie |
| **Full duplex** | Two | **Yes** | 2 (xmit and rcv) | Phone call |

At the session layer this is about the **conversation's** rules, not just the wire. A login prompt is a turn-taking dialogue (you type, the server answers), even when the cable underneath is full duplex.

Next, a check on the three modes.
