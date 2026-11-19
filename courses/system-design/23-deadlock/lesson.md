# Deadlock

*Chapter 1 · Foundations.*

## Deadlock

Take two bank accounts, each with its own lock. A transfer locks the source, then the target. Now two transfers run at once in opposite directions:

```text
Thread A: transfer(x → y)         Thread B: transfer(y → x)
lock x                            lock y
wait for y ...                    wait for x ...       forever
```

Each holds the lock the other needs. Neither will ever let go. That's a **deadlock**. It needs four conditions together: mutual exclusion, holding one resource while waiting for another, no forcible taking of locks, and a **cycle** of waiting. Break any one and deadlock is impossible. The usual fix breaks the cycle with **lock ordering**: every thread takes locks in the same global order, such as lowest account id first. Then no cycle can form.

Databases face the same problem with row locks. They detect the cycle and abort one transaction, which your application must retry.

Next, a short check on what you just read.
