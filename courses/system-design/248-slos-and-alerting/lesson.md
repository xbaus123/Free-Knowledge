# SLOs and Alerting

*Chapter 10 · Observability and the Capstone.*

## SLOs and alerting

You can't page a human for every anomaly. Alert on **symptoms users feel**, not on causes like CPU usage.

- An **SLI** (service level indicator) is a measurement: the fraction of requests that succeed in under 300 ms.
- An **SLO** (objective) is a target for it: 99.9% over 30 days.
- The **error budget** is what the SLO allows to fail: 0.1% of requests, about 43 minutes of total outage a month. Spending it on risky launches is fine. Running out means slowing down and fixing reliability.

The **burn rate** is how fast you're spending the budget: the observed error ratio divided by the allowed ratio (1 − SLO). A burn rate of 1 spends exactly the whole budget over the SLO window. A burn rate of 14.4 spends 2% of a 30-day budget in one hour, and would exhaust it in about two days.

**Multi-window burn-rate alerts** (from Google's SRE workbook) page when *both* a long window (say 1 hour) and a short window (say 5 minutes) burn above a threshold. The long window ensures enough budget was spent to matter, so a brief blip doesn't page anyone. The short window ensures the problem is still happening, so the alert clears quickly after recovery.

Next, a short check on what you just read.
