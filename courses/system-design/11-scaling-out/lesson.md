# Scaling Out: The Single Point of Failure

Your app just got featured on the front page. Traffic jumped from a trickle to **1,000 requests per second** (80% reads, 20% writes), and every one of them lands on a single API server.

Do the back-of-the-envelope math from the last lesson. The server has **4 workers**, and each request takes **6 ms** of work, so it can finish about 4 ÷ 0.006 ≈ **667 requests per second**. Demand is 1,000. That's 150% utilization: a queue that grows every millisecond, and response times that climb from milliseconds into hundreds of milliseconds.

## Scale up or scale out?

From lesson 1, you have two options:

- **Scale up**: give the server a bigger connection pool. It works, but bigger machines cost disproportionately more.
- **Scale out**: put a **load balancer** in front of several ordinary servers. It spreads requests across them, and if one dies, health checks notice and the rest keep serving. Scaling out also improves **reliability**: with one server, one crash takes the whole app down. That server is a **single point of failure**.

The next lesson opens up the load balancer itself: its algorithms, its health checks, and how it grows into an API gateway.

## Your task

Keep **p99 latency at or under 200 ms** during the spike, on a budget of **$95/month**.

| Component | Cost |
|---|---|
| Load Balancer | $20 |
| API Server (4-connection pool) | $10, plus $10 per extra connection |
| Database | $50, plus $40 for a standby replica |

1. Add a **Load Balancer** between the Client and your servers.
2. Add a **second API Server** behind it, and connect both servers to the Database.
3. Click **Simulate Traffic** to send 1,000 requests through your design. Then use the timeline under the canvas to replay it: nodes glow amber when busy and red near capacity, and busy connections thicken.

Drag from a node's right handle to another node's left handle to connect them. Select a node or connection and press Backspace to delete it. **Double-click** a node to change its settings.

## Reading the results

- **p50 vs. p99**: with enough capacity they're close together. When a server is overloaded, p99 shoots up first, because the requests at the back of the queue wait longest.
- **CPU**: a server busy 95% or more of the run can't keep up with demand.
- **Monthly cost**: shown in the corner of the canvas as you build.

> **Experiment.** Once you pass, open the **⚡ Chaos** toolkit and crash one of your servers. Requests in flight on it fail, and the load balancer takes about 100 ms to notice. The surviving server now carries everything. Is it enough?
>
> Then crash the **Database**. Everything fails: it's still a single point of failure. Double-click it and add a **synchronous** standby, then crash it again: it fails over in 150 ms without losing data. Try **asynchronous**: no extra latency, but writes it confirmed in the last 50 ms are lost. That's the replication trade-off you'll study in Part II. (Chaos runs are experiments; they don't affect your progress.)
