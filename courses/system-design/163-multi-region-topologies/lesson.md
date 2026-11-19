# Multi-Region Topologies

*Chapter 6 · Partitioning and Geography.*

## Multi-region topologies

From simplest to most ambitious:

| Topology | Writes go to | Reads served | On region loss | Hard part |
|---|---|---|---|---|
| **Single region + CDN** | The one region | Static content at the edge; the rest from the region | Down | Distant users wait on every dynamic request |
| **Active-passive** (warm standby) | The primary region | The primary region | Promote the standby: RPO = lag, RTO = minutes | Standby capacity sits idle; failover is rarely exercised, so it often doesn't work |
| **Read local, write global** | One leader region | Every region, from local followers | Promote a follower in another region | Writes from far away are slow; reads may be stale |
| **Geo-partitioned** (home region per user) | Each user's home region | The home region, or anywhere if slightly stale is fine | That region's users fail over or wait | Users who move, and data shared between users in different regions |
| **Multi-leader** (active-active) | Any region | Any region | Others keep going | **Write conflicts** |
| **Globally consensus-replicated** | A leader per partition, agreed by quorum across regions | Any region, with a consistency choice | A quorum survives the loss of one region | Every write waits for a cross-region round trip |

## Read local, write global

The single-leader replication of chapter 5, stretched across regions. The leader sits in one region, and every region has followers. Reads are fast everywhere, and writes travel to the leader. It works well for read-heavy workloads, but the replication-lag anomalies you saw in chapter 5 grow from milliseconds to hundreds of milliseconds. A user who writes in Sydney and reads back from the Sydney follower may not see their own write, so route a user's reads to the leader for a few seconds after they write (**read-your-writes**).

## Geo-partitioning

Give every user a **home region**, and keep their data there. A European user's profile, orders, and messages live in Frankfurt, and all writes for them go to Frankfurt. This is partitioning (earlier in this chapter) with geography as the partition key. It avoids write conflicts entirely, because each record has exactly one leader, and it's the natural way to satisfy data residency rules. CockroachDB's `REGIONAL BY ROW` tables and Spanner's placement rules do this at the database level. The trouble is data that doesn't belong to one user: a group chat with members on three continents, or a global product catalog. Those need a home too, or one of the other topologies.

Next, a short check on what you just read.
