# Describing Load and Performance

*Chapter 1 · Foundations.*

## Scalability: coping with more load

"Does it scale?" is meaningless on its own. The useful question is: *if load grows in a particular way, what happens to performance, and what can we add to cope?*

## Describing load: load parameters

**Load parameters** are the numbers that describe the load on your system. Which ones matter depends on the architecture:

- Requests per second to a web server
- The ratio of reads to writes in a database
- Simultaneously active users in a chat room
- Cache hit rate
- **Fan-out**: how many downstream requests one incoming request causes

Twitter is the classic example. Posting a tweet is rare (about 4,600 per second on average in 2012, 12,000 at peak). Reading home timelines is common (300,000 per second). The hard part is **fan-out**. Each tweet has to reach every follower's timeline. Twitter switched from assembling timelines when you read them to pushing each new tweet into followers' cached timelines when it's written. Reads got cheap, and writes got expensive. For the few accounts with tens of millions of followers, that write fan-out was too costly, so those tweets are merged in at read time instead. The **distribution of followers per user** turned out to be a key load parameter. You'll design this system in the capstone.

## Describing performance

Two ways to look at it:

- **Throughput**: how many requests (or records, or bytes) the system processes per second. This matters most for batch work.
- **Response time**: how long a client waits from sending a request to getting a response. This matters most for online services.

People often say **latency** for response time. Strictly, latency is the time a request spends *waiting* to be handled. Response time is everything the client sees: service time plus network delays plus queueing delays.

Response time isn't one number. Run the same request a thousand times and you get a **distribution**. Some requests are slow because of a garbage collection pause, a lost packet that had to be retransmitted, or a cold cache.

Next, a short check on what you just read.
