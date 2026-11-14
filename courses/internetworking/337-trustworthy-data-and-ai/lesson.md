# Trustworthy Data and AI

*Chapter 10 · Resilience.*

More and more decisions are made by **AI and machine learning** models trained on data. A model is only as trustworthy as its data, which gives attackers a new target: not the server, but what the model **learns** and **sees**.

## What trustworthy data needs

- **Attributes, metadata, and documentation**: where the data came from and what it means.
- **Access control** policies, and **auditing** of every access.
- **Protected processing pipelines**: the steps from raw data to a trained model.
- Watching for **privacy leakage**: a model can memorize and reveal its training data.
- **Lineage**: the data's history, from origin through every change.
- **Legitimate access to APIs**, and care with **third-party dependencies** (the supply chain again).

## Threats

| Threat | What happens |
|---|---|
| **Data poisoning** | Bad examples slipped into the **training** data, so the model learns the wrong thing |
| **Manipulating quantities** | **Flooding** the data with fake examples, or **restricting** it so some cases are missing |
| **Model manipulation** | Changing the model itself, or its settings |
| **Adversarial perturbations** | Tiny changes to an **input** that flip the model's answer |

Poisoning attacks the model while it **learns**. Adversarial perturbations attack it while it **decides**.

## Adversarial perturbations

Take a clean input and add a small change, **imperceptible to a human**, but enough to change the model's prediction. Change a few pixels and a stop sign is read as a speed limit sign. Change one word and a malicious email is read as safe. Some perturbations are **input-agnostic**: the same small pattern fools the model on almost any input.

Two kinds of attack:

- **White-box**: the attacker has **full access** to the model, its design and weights, and can calculate exactly which change works.
- **Black-box**: **no access** to the model. The attacker sends inputs, watches the outputs, and **infers** what fools it.

## Resilient AI and ML

- **Robustness**: training on adversarial examples so the model learns to resist them, threat detection, vulnerability assessment, incident response, data protection.
- **Resourcefulness**: optimizing resources, **adaptive** security policies, AI-based threat hunting, **data masking** (hiding sensitive fields from those who don't need them).
- **Redundancy**: data replication, high availability, multiple data centers, automated failover.
- **Rapidity**: network traffic analysis, automated patching, threat intelligence, dynamic risk assessment, predictive analytics.

## The human element

An old communication model (Gerbner's) separates the **event** that happens, how a person or machine **perceives** it, and the **message** they then produce. Attacks can work at any step: fake the event, fool the perception, or change the message.

That applies to people as much as models. A thought from the slides: if AI is so smart, why do we train **humans to think like computers** in security training, instead of AI to understand humans? The answer is partly that AI isn't really smart, and partly that humans are hard to understand. Either way, people stay part of the system, and security has to work **with** how they actually behave.

Next, a check.
