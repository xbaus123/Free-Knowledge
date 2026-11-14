# DNS Queries and Responses

*Chapter 7 · DNS.*

A DNS query and its response use the **same message format**: five sections, some of them empty.

| Section | Holds |
|---|---|
| **Header** | An ID, the opcode, and flags. Whether this is a query or response, whether the answer is authoritative |
| **Question** | What's being asked: **QNAME**, **QCLASS**, **QTYPE** |
| **Answer** | Records that answer the question |
| **Authority** | Records pointing to the authoritative servers (NS records in a referral, or the SOA when there's no answer) |
| **Additional** | Records that help, like the addresses of the nameservers in the authority section |

## An example from the RFC

The query for `SRI-NIC.ARPA`'s address:

```
Header     | OPCODE=SQUERY
Question   | QNAME=SRI-NIC.ARPA., QCLASS=IN, QTYPE=A
Answer     | <empty>
Authority  | <empty>
Additional | <empty>
```

The response from the server C.ISI.EDU:

```
Header     | OPCODE=SQUERY, RESPONSE, AA
Question   | QNAME=SRI-NIC.ARPA., QCLASS=IN, QTYPE=A
Answer     | SRI-NIC.ARPA. 86400 IN A 26.0.0.73
           |               86400 IN A 10.0.0.51
Authority  | <empty>
Additional | <empty>
```

Notice:

- The response **copies the question back**, so the client can match it with what it asked. A 16-bit **ID** in the header does the same job.
- **RESPONSE** marks it as an answer, and **AA** means **authoritative answer**: C.ISI.EDU runs the zone, so this didn't come from a cache.
- The host has **two A records**: it was on two networks, so it had two addresses.

## Query types beyond record types

A **QTYPE** can be any record type (A, MX, NS ...), plus a few that only make sense in a question:

| QTYPE | Asks for |
|---|---|
| **AXFR** | A **zone transfer**: the entire zone, every record. Over TCP |
| **MAILB** | All mailbox-related records (MB, MG, MR) |
| **MAILA** | Mail agent records. **Obsolete** (replaced by MX) |
| **\*** | **All** records for the name (often written ANY) |

AXFR is how secondaries copy a zone. It's also an attacker's favorite question, as you'll see in the security lesson.

Next, a check on messages.
