# Task Queues

*Chapter 9 · Microservices and Data Flow.*

## Family 1: Task queues (traditional message brokers)

RabbitMQ (the AMQP standard), ActiveMQ, and Amazon SQS behave like a queue of individual messages:

- A consumer **receives** a message, processes it, and **acknowledges** it. Only then does the broker **delete** it.
- If the consumer crashes or doesn't acknowledge in time, the broker **redelivers** the message to another consumer. In SQS, a received message is hidden for a **visibility timeout**. If it isn't deleted before the timeout ends, it reappears.
- Messages are deleted once processed, so the broker holds only the backlog and works best when queues are short. Slow consumers make the queue grow, and throughput degrades as it spills to disk.
- Brokers can **route** flexibly. RabbitMQ's exchanges send a message to queues by exact key, by topic pattern (`orders.*.eu`), or to all bound queues.
- Extras: per-message **delays**, **priorities**, and **dead-letter queues**.

Consequences to design around:

- **At-least-once delivery.** A consumer can finish the work and then crash before its acknowledgment arrives, or run past the visibility timeout. The broker redelivers, and the work happens twice. So consumers must be **idempotent**: charge the card only if this payment id hasn't been charged.
- **A late acknowledgment can be refused.** If the visibility timeout expired and another consumer received the message, the first consumer's acknowledgment is for a delivery that no longer counts. (It's the lease problem from chapter 7 again.) Long tasks must **extend** their visibility timeout as they go.
- **Ordering is lost.** With competing consumers and redelivery, message 2 can finish before message 1. Even a single consumer sees reordering when a message is redelivered after later ones were processed.
- **Poison messages**: a message that crashes its consumer every time would be redelivered forever, blocking capacity. After N failed deliveries, move it to a **dead-letter queue (DLQ)** for a human to inspect.

Next, a short check on what you just read.
