# Hardware Resilience

*Chapter 10 · Resilience.*

The rest of the chapter applies the four Rs, one area at a time, starting at the bottom: the physical boxes.

**Hardware resilience** is the capacity of a physical device or system to endure and recover from faults or disturbances while keeping its critical functions. It matters most where downtime is disastrous: critical infrastructure, industrial systems, aerospace, cars, hospitals.

## Robustness

- **Enterprise-grade** systems: server hardware with ECC memory, dual power supplies, and parts rated for 24/7 use, not desktop parts.
- **Uptime** as the measure.
- Proper **server rooms** and **communication closets**: cooling, clean power, locks (chapter 2's physical security).
- **Preventing and detecting unauthorized** systems and components: a rogue access point or a keylogger plugged in behind a desk.
- **Hardware refreshes**: replacing equipment before it ages out of support or reliability.
- **Anti-tampering**: tamper-evident film and seals on cases and ports, so you can tell if a box has been opened.

## Resourcefulness

- **Scalable architecture**: components can be **swapped or added** to handle more load.
- **Ghost systems**: pre-built standby machines, or ready disk images, that can be put in place of a failed machine quickly. (The name comes from Ghost, an old disk-imaging tool.)

## Redundancy

**RAID** (redundant array of independent disks) spreads data across several drives:

| Level | How | Min drives | Usable space | Drives that can fail |
|---|---|---|---|---|
| RAID 0 | Striping, no copies | 2 | All of it | **None**: speed only, not redundancy |
| **RAID 1** | **Mirroring**: every drive holds the same data | 2 | One drive's worth | All but one |
| **RAID 5** | Striping with **parity** spread across drives | 3 | All but one drive | **One** |
| RAID 6 | Striping with two parity blocks | 4 | All but two drives | Two |

RAID 5's parity is an **XOR** of the data blocks. Lose any one drive, and XOR of everything that's left rebuilds it. You'll code this later in the chapter.

RAID protects against a **dead drive**, not against deleting a file or ransomware encrypting it: those changes are copied to every drive instantly. RAID is not a backup.

Other redundancy:

- **Hot sites and cold sites**: a second location to run from.
  - A **hot site** is fully equipped and running, with current data. It can take over in minutes to hours. Expensive.
  - A **cold site** has space, power, and network, but no equipment or data. Days to weeks to bring up. Cheap.
  - A **warm site** sits in between: equipment, but data that has to be restored.
- **Multiple internet connections**, ideally from **different providers** over different physical routes.
- **Clusters**, and ghost systems again.

## Rapidity

- **Hot-swap drives**: pull the dead drive and slide in a new one **without powering down**. The RAID rebuilds while the server keeps working.
- **Data centers with automated failover**, and **traffic redirected** to the healthy site.

Next, a check.
