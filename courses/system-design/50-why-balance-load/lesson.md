# Why Balance Load

*Chapter 2 · The Front Door.*

In the scaling-out lab, you put a load balancer in front of two servers and the latency spike went away. That box did more than you might think. It decided which server got each request, noticed when one died, and hid from clients how many servers there were. The next few readings open the box: where load balancing happens, how the algorithms differ, how health checking works, and how a load balancer grows into a reverse proxy and then into an API gateway.

## Why balance load

A load balancer sits between clients and a pool of interchangeable **backends** and gives you three things:

1. **Scalability**: add a server, and the pool's capacity grows. Clients don't change anything.
2. **Availability**: when a backend dies, traffic flows to the others. Without a load balancer, every client pointed at the dead server fails.
3. **Indirection**: clients know one stable address. Behind it, you can deploy, resize, and replace servers freely. Most of the operational tricks in this course (rolling deployments in chapter 4, canary releases, failover) depend on this layer of indirection.

It only works cleanly when the backends are **stateless**: any server can handle any request because the state lives elsewhere, in a database or cache. Keeping session state on a server forces **sticky sessions** (routing each user back to "their" server), which spreads load unevenly and loses sessions when that server dies. Move the state out and the servers become cattle, not pets.

Next, a short check on what you just read.
