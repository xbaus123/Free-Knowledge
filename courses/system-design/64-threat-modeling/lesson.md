# Threat Modeling

*Chapter 2 · The Front Door.*

The gateway you built in the load balancer lab checked a bearer token against a fixed set of API keys. That works for a handful of trusted scripts, but not for a million users, a mobile app, third-party integrations, and dozens of internal services that all need to know **who is calling** and **what they may do**. The security readings are about building that trust across a network: encrypting traffic with TLS, establishing identity with OAuth 2.0 and OpenID Connect, carrying it in signed tokens, and deciding what each identity may do.

Security isn't a feature you bolt on at the end. Like reliability, it's a property of the whole system. A design is only as secure as its weakest trust boundary.

## Start with a threat model

Before choosing tools, decide what you're defending against. **Threat modeling** asks four questions:

1. **What are we building?** Draw the data flows: clients, gateway, services, databases, queues, third parties.
2. **What can go wrong?** Look hardest at the **trust boundaries**, the lines data crosses between parties that trust each other differently: the internet to your edge, your edge to internal services, your services to a vendor's API.
3. **What are we doing about it?**
4. **Did we do a good job?**

Microsoft's **STRIDE** mnemonic is a checklist for question 2. Each threat violates one security property, and each has typical defenses:

| Threat | Violates | Example | Typical defense |
|---|---|---|---|
| **S**poofing | Authenticity | Logging in with a stolen session cookie | Authentication, MFA, short-lived tokens |
| **T**ampering | Integrity | Editing a token's `role` claim to `admin` | Signatures, MACs, TLS |
| **R**epudiation | Non-repudiation | "I never issued that refund" | Tamper-evident audit logs |
| **I**nformation disclosure | Confidentiality | Reading traffic on café Wi-Fi; a leaky error message | Encryption in transit and at rest, least privilege |
| **D**enial of service | Availability | A flood of expensive search requests | Rate limiting (chapter 6), quotas, autoscaling |
| **E**levation of privilege | Authorization | A customer calling an admin-only endpoint | Authorization checks on every request |

Three principles run through every defense:

- **Least privilege**: every user, service, and key gets the minimum access it needs, for the minimum time.
- **Defense in depth**: assume any one layer will fail. Encrypt *and* authenticate *and* authorize *and* audit.
- **Fail closed**: when a check can't be completed (the key is unknown, the policy service is down, the token is malformed), deny. A system that fails open turns every outage into a breach.

Next, a short check on what you just read.
