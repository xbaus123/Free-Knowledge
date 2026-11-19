# Scaling Approaches and Maintainability

*Chapter 1 · Foundations.*

## Approaches to scaling

- **Scaling up (vertical)**: a more powerful machine. It's simple, but big machines cost disproportionately more and have a ceiling.
- **Scaling out (horizontal)**: more machines sharing the load (a **shared-nothing** architecture). There's no ceiling, but stateful parts like databases become much harder.
- **Elastic** systems add capacity automatically as load rises.

Stateless services (like API servers) are easy to scale out behind a load balancer. **Data** is the hard part. That's why most of this course is about replicating, partitioning, and moving data.

## Maintainability

Most of a system's cost comes after launch: fixing bugs, keeping it running, adapting it to new needs. Three principles help:

- **Operability**: easy for operators to keep running, with good monitoring, predictable behavior, and sane defaults.
- **Simplicity**: managing complexity with good **abstractions** that hide implementation details behind clean interfaces.
- **Evolvability**: easy to change. You'll see this again with schema evolution and rolling deployments.

## Key terms

| Term | Meaning |
|---|---|
| Fault vs. failure | One component misbehaving vs. the whole system failing users |
| Load parameter | A number describing load: requests/s, read:write ratio, fan-out |
| Throughput | Work completed per second |
| Response time | What the client waits; includes queueing and network delays |
| p50 / p99 | The response time 50% / 99% of requests beat |
| Tail latency | The slow end of the distribution (p99 and beyond) |
| Utilization | The fraction of a resource's capacity in use |
| Scale up / scale out | Bigger machine / more machines |

Next, a short check on what you just read.
