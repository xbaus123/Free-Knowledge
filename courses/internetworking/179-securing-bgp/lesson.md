# Securing BGP

*Chapter 6 · Routing.*

There are two questions you can ask about a BGP announcement:

1. **Origin validation**: is the AS at the end of the path actually **authorized** to announce this prefix?
2. **Path validation**: did the announcement **really travel** through the ASes listed in its path?

The 2008 YouTube hijack would have been stopped by origin validation alone. A cleverer attacker who keeps the right origin but forges the path needs path validation.

## Four approaches

| | Validates | How | Overhead | Status |
|---|---|---|---|---|
| **S-BGP** (Secure BGP) | Origin **and** path | Hierarchical PKI: certificates for every AS and prefix | **High**; impractical in dynamic environments like the cloud | Legacy, never deployed widely |
| **soBGP** (Secure Origin BGP) | Origin; path **feasibility** only | **Web of trust**: ASes vouch for their peers, no central authority. Separate security messages | Low | Legacy |
| **RPKI** (Resource Public Key Infrastructure) | **Origin** only | RIRs sign **ROAs**. Out-of-band, so **no changes to BGP** | Low | **Widely adopted** |
| **BGPsec** | **Path** (cryptographically) | Every AS **signs** the path. `AS_PATH` replaced by `BGPsec_Path`. Builds on RPKI | **Significant**, and hard to use | Standardized, barely deployed |

soBGP's "feasibility" check means it confirms a path is **possible** (those ASes really are neighbors), not that the update actually went that way.

## RPKI in practice

A prefix holder asks its RIR to sign a **Route Origin Authorization (ROA)**: "AS 64500 may originate 203.0.113.0/24, and anything inside it up to /25." The ROAs are published, and routers download them **outside of BGP** (that's what *out-of-band* means). When an announcement arrives, the router compares it:

| Result | Meaning | Typical action |
|---|---|---|
| **Valid** | A ROA covers it and the origin AS matches | Accept |
| **Invalid** | A ROA covers the prefix, but the AS or length is wrong | **Drop** |
| **Not found** | No ROA covers the prefix | Accept (most prefixes still have none) |

A hijacker announcing YouTube's space from their own AS would come back **invalid**.

## Why we still don't have everything

RPKI is cheap and needs no protocol change, so it spread. Full path validation needs every AS on the path to sign, in real time, on every update: expensive, and useless until nearly everyone does it. So today's Internet has **good origin validation and little path validation**.

Next, a check on securing BGP.
