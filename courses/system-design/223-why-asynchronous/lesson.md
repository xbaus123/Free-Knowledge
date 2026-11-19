# Message Brokers: Why Go Asynchronous

*Chapter 9 · Microservices and Data Flow.*

*Based on* Designing Data-Intensive Applications*, Chapter 11.*

So far, every interaction in your designs has been a **request and response**: a caller sends a request, waits, and gets an answer. That couples the two sides in time. If the receiver is slow, the caller waits. If it's down, the caller fails. If a thousand callers arrive at once, the receiver must handle a thousand requests at once.

A **message broker** breaks that coupling. A **producer** hands a message to the broker and moves on. A **consumer** takes it from the broker whenever it's ready. The broker is a buffer, a router, and a durable record in between. The next few readings cover the two very different families of broker, how they distribute work, and what "delivered" really means.

## Why go asynchronous

- **Load leveling**: a burst of 10,000 sign-ups becomes a queue that workers drain at their own pace. The capstone uses exactly this: tweets are acknowledged at once, and the expensive fan-out happens behind a queue. So do the choreographed sagas from the microservices readings, where each service reacts to the previous one's events.
- **Decoupling**: the producer doesn't know or care who consumes, how many consumers there are, or whether they're up right now.
- **Fan-out**: one event ("order placed") feeds many independent consumers: email, inventory, analytics, search.
- **Reliability**: if a consumer crashes mid-task, the broker redelivers the message to another one.

The cost: the producer no longer learns the outcome. "Accepted" isn't "done," and errors surface later and elsewhere, so you need dead-letter handling, monitoring of queue depth, and idempotent consumers.

## Two questions every messaging system answers

*Designing Data-Intensive Applications* frames any messaging system with two questions:

1. **What happens when producers send faster than consumers can process?** The system can **drop** messages, **buffer** them in a queue (in memory? on disk? what happens when that fills?), or apply **backpressure**, blocking the producer until there's room (TCP flow control and bounded Unix pipes do this).
2. **What happens when nodes crash or go offline?** Are messages lost? Durability means writing to disk and replicating, which costs throughput. Some applications (metrics sampling) can tolerate occasional loss, and others (payments) can't.

## Patterns: point-to-point and publish-subscribe

When several consumers read from one stream of messages, there are two basic patterns:

- **Load balancing (competing consumers, point-to-point)**: each message goes to **one** of the consumers. Add consumers to process faster. This is a **work queue**: resize images, send emails, charge cards.
- **Fan-out (publish-subscribe)**: each message goes to **all** subscribers. Each subscriber does something different with every event.

Real systems combine them: several independent *groups* each receive every message (fan-out), and within each group, consumers share the work (load balancing). AWS's classic pattern publishes to an SNS topic that fans out to several SQS queues, each drained by its own pool of workers.

Next, a short check on what you just read.
