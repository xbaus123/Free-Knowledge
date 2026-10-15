# Reliability & Scalability: The Single Point of Failure

Your app just got featured on the front page. Traffic jumped from a trickle to **1,000 requests per second**, and every one of them lands on a single API server.

That server can handle about **667 requests per second**: 4 worker threads, each needing 6 ms per request. The rest wait in a queue that grows every second, so response times climb from milliseconds into hundreds of milliseconds. Users notice, and they leave.

## Describing load and performance

*Designing Data-Intensive Applications* (Chapter 1) suggests two questions:

- **What is the load?** Here: 1,000 requests arriving over one second.
- **How does performance hold up?** Averages hide pain, so look at **percentiles**. The **p99** response time is the latency that 99% of requests beat. The slowest 1% are often your most active users.

When a machine can't keep up, you can **scale up** (buy a bigger machine) or **scale out** (spread the load across several machines). Scaling out also improves **reliability**: with one server, a single crash takes the whole app down. That server is a *single point of failure*.

## Your task

Keep **p99 latency at or under 200 ms** during the spike, on a budget of **$95/month**.

| Component | Cost |
|---|---|
| Load Balancer | $20 |
| API Server (4-connection pool) | $10, plus $10 per extra connection |
| Database | $50, plus $40 for a replica |

You could buy one big server with a larger pool (scaling up), but bigger machines cost disproportionately more. Scaling out is cheaper here:

1. Add a **Load Balancer** between the Client and your servers. It spreads requests evenly.
2. Add a **second API Server** behind it, and connect both servers to the Database.
3. Click **Simulate Traffic** to send 1,000 requests through your design, then use the timeline under the canvas to replay it.

Drag from a node's right handle to another node's left handle to connect them. Select a node or connection and press Backspace to delete it. **Double-click** a node to change its settings.

> Once you pass, open the **Chaos** toolkit and crash one of your servers. What happens to the requests in flight, and to the server that's left? Then crash the Database. Is there still a single point of failure? (Chaos runs are experiments; they don't affect your progress.)
