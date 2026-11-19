# Why Go Multi-Region

*Chapter 6 · Partitioning and Geography.*

*Based on* Designing Data-Intensive Applications*, Chapters 5 and 6.*

*Based on* Designing Data-Intensive Applications*, Chapters 5 and 6.*

Everything you've built so far lives in one data center. Replicas protect you from a failed disk or machine, and partitions spread load across racks. But the whole system still shares one building, one power grid, one network provider, and one spot on the map. The next readings spread it across the planet: running in several regions at once, steering each user to the right one, keeping their data where the law says it must stay, and pushing content to the edge of the network with a CDN.

## Why go multi-region

Three forces push a system out of a single region.

**Latency.** Light in optical fiber travels about 200,000 km per second, roughly 200 km per millisecond. New York to London is about 5,600 km, so the round trip can't be faster than 56 ms, and in practice it's about 70. Sydney to Virginia is closer to 200 ms. Chapter 1 showed that opening an HTTPS connection costs several round trips before the first byte arrives, so a user on the far side of the world waits most of a second for a page that a nearby user gets in 100 ms. No amount of server capacity fixes the speed of light. Only moving the servers closer does.

**Availability.** Whole regions fail: a power event, a cooling failure, a bad configuration push to a regional control plane, a fiber cut. Every major cloud has had multi-hour regional outages. If your only region goes down, so do you, however many replicas you have inside it.

**Regulation.** Many jurisdictions restrict where personal data may be stored and processed. Some customers, especially governments, banks, and hospitals, require it contractually. You can't serve them from a single region on another continent.

The costs are real too: more infrastructure (each region needs enough capacity to be useful), cross-region bandwidth bills, much harder data consistency, and deploys and incidents that span time zones.

## Disaster recovery vocabulary

Two numbers describe what a regional failure costs you:

- **RPO** (recovery point objective): how much recently written data you can afford to lose. With asynchronous replication to another region, it's the replication lag, typically seconds.
- **RTO** (recovery time objective): how long until you're serving again in another region. It ranges from hours (restore from backups) to seconds (traffic is already flowing there).

Next, a short check on what you just read.
