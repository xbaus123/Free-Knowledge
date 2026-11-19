# Round Robin and Least Connections

*Chapter 2 · The Front Door.*

## Algorithms

Every algorithm answers one question: which healthy backend gets the next request?

## Round robin

Take turns: A, B, C, A, B, C. It's simple, stateless apart from a counter, and perfectly fair *if every request costs the same and every server is equally fast*. Neither is usually true.

## Weighted round robin

Give bigger servers bigger weights. With weights A=5, B=1, C=1, A gets 5 of every 7 requests. A naive version sends A five in a row, then B, then C: a burst that briefly overloads A. NGINX's **smooth weighted round robin** interleaves them instead:

1. Every server keeps a running score, starting at 0.
2. On each pick, add each server's weight to its score.
3. Choose the server with the highest score (ties go to the first), then subtract the total weight from its score.

For A=5, B=1, C=1, that yields A, A, B, A, C, A, A: the same proportions, spread evenly.

## Least connections

Send each request to the backend with the **fewest active requests**. This adapts automatically to real conditions:

- Requests vary in cost: a search takes 500 ms and a profile fetch 5 ms.
- Servers vary in speed: one has a noisy neighbor, a cold cache, or a long garbage collection pause.

Round robin keeps sending a slow server its full share, so requests pile up there and the tail latency explodes (remember queueing, chapter 1). Least connections notices the pile-up, because a slow server's requests stay active longer, and steers around it. The cost is state: the balancer must count active requests per backend, which is easy in one process and hard to share across many balancer instances.

Variants weigh in response time (**least response time**, or an **EWMA**, an exponentially weighted moving average of latency, as used by Linkerd and Envoy).

Next, a short check on what you just read.
