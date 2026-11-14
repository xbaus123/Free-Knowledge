# Synchronization and Checkpoints

*Chapter 9 · Upper Layers.*

Two more session-layer jobs keep long conversations healthy: keeping streams **in step**, and being able to **pick up where you left off**.

## Synchronization

A session often carries more than one stream. A video call has an **audio** stream and a **video** stream, and they travel separately. If the video packets are delayed, the picture falls behind the sound and lips stop matching words.

The fix is to **insert timestamps into the data flow**. Each chunk is stamped with when it was captured. The receiver lines up chunks with matching timestamps and, if one stream lags behind another, it **resynchronizes**: it holds the faster one back, or skips ahead in the slower one.

You've seen this in:

- **Lip sync** in video calls and streaming.
- **Games**, where every player's actions are stamped so the server can put them in the right order.

## Checkpointing and recovery

A long transfer that fails at 95% shouldn't have to start again from zero. **Checkpoints** are **re-entry points** marked during the session. If the session is interrupted, both sides go back to the last checkpoint and carry on from there.

- **Resuming a download**: the browser asks the server for "the bytes from 734 MB onward" instead of the whole file again.
- **Database transactions**: work is committed at known points, so a crash rolls back to the last consistent state.
- **Games**: reconnect after a dropped connection and you're put back into the same match, not a new one.

The trade-off: more checkpoints mean **less work lost** after a failure, but **more overhead** while everything is going well.

Next, a check on synchronization and checkpoints.
