# SPF, DKIM, and DMARC

*Chapter 8 · Mail.*

Spoofing works because SMTP takes the sender's word for who they are. Three standards, all published in **DNS TXT records**, let a receiving server check.

## SPF: who may send

**Sender Policy Framework** lists the servers allowed to send mail for a domain:

```
example.com.  IN  TXT  "v=spf1 ip4:198.51.100.20 include:spf.protection.outlook.com -all"
```

Read it as: "198.51.100.20 may send for me, so may whatever Microsoft 365 lists, and **everyone else fails**." The ending sets how strict it is: **`-all`** means fail, **`~all`** means soft fail (accept but mark as suspicious), and `?all` means no opinion.

The receiver checks the **envelope** domain (`MAIL FROM:`) against the connecting server's IP. The weak points: SPF doesn't look at the `From:` header people actually see, and it usually breaks when mail is **forwarded**, because the forwarder's IP isn't on the list.

## DKIM: a signature

**DomainKeys Identified Mail** has the sending server **sign** the message with a private key and add the signature as a header:

```
DKIM-Signature: v=1; a=rsa-sha256; d=example.com; s=sel1; h=from:to:subject:date; bh=...; b=...
```

The receiver fetches the **public key** from DNS, at `selector._domainkey.domain`, here `sel1._domainkey.example.com`, and checks the signature. If it's valid, the signed headers and body haven't been changed since they left `example.com`. Because the signature travels **inside** the message, DKIM usually survives forwarding.

## DMARC: the policy

SPF and DKIM each prove something about *a* domain, but not necessarily the one in the `From:` header. **DMARC** (Domain-based Message Authentication, Reporting, and Conformance) ties them to it:

```
_dmarc.example.com.  IN  TXT  "v=DMARC1; p=reject; rua=mailto:dmarc@example.com"
```

- A message **passes** DMARC if SPF or DKIM passes **and** that domain **aligns with** (matches) the `From:` header's domain.
- **`p=`** says what to do with failures: **`none`** (just report), **`quarantine`** (send to spam), or **`reject`**.
- **`rua=`** asks receivers to send daily **reports**, so the domain owner can see who's sending as them.

The usual rollout: start at `p=none`, read the reports until every legitimate sender passes, then move to `quarantine` and finally `reject`.

| | Checks | Published at | Survives forwarding? |
|---|---|---|---|
| **SPF** | The sending server's IP | `domain` TXT | Usually not |
| **DKIM** | A signature on the message | `selector._domainkey.domain` TXT | Usually |
| **DMARC** | That SPF or DKIM matches the `From:` domain, and what to do if not | `_dmarc.domain` TXT | Uses the other two |

Next, a check on SPF, DKIM, and DMARC.
