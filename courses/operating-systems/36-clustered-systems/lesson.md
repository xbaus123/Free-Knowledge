# Clustered Systems

*Chapter 1 · Part 3: Computer-System Architecture.*

A multiprocessor puts several CPUs in **one** computer. A **clustered system** goes a step further: it gathers **multiple whole computers** working together. Each computer in the cluster (a **node**) is usually a multicore system itself.

## Loosely coupled

Clusters are **loosely coupled**: each node has its own memory and OS, and they're linked by a network or a fast **interconnect**. They usually **share storage** through a **storage-area network (SAN)**: a private network that lets many machines reach the same disks.

```
 [ computer ] ── interconnect ── [ computer ] ── interconnect ── [ computer ]
       │                               │                               │
       └───────────────────── storage-area network ────────────────────┘
```

## High availability

The main reason to cluster is **high availability**: a service that **keeps running even if one or more machines fail**. Each node runs a little software that watches the others over the network. If a node stops responding, another takes over its storage and restarts its applications. Users notice only a brief interruption.

There are two ways to arrange it:

| | Asymmetric clustering | Symmetric clustering |
|---|---|---|
| How it works | One machine runs the applications; another sits in **hot-standby mode**, doing nothing but monitoring the active one | **Multiple nodes run applications** and **monitor each other** |
| On failure | The standby takes over | The others take over the failed node's work |

## High-performance computing

Some clusters exist for raw power instead: **high-performance computing (HPC)**. Hundreds or thousands of nodes work on one problem at once: weather forecasts, physics simulations, training AI models.

The catch: **applications must be written to use parallelization**. That means dividing a program into pieces that run on separate nodes at the same time, then combining the results. An ordinary program runs on one node only, however big the cluster.

## Distributed lock manager

When several nodes share the same disks, two of them could change the same data at once and corrupt it. Some clusters use a **distributed lock manager (DLM)** to **avoid conflicting operations**: before a node touches shared data, it takes a lock, and other nodes wait.

Next, a check on clusters.
