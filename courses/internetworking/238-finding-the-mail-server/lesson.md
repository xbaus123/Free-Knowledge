# How Mail Knows Where to Go

*Chapter 8 · Mail.*

An email address has two halves: `bob@example.com` is the **mailbox** (`bob`), then `@`, then the **domain** (`example.com`). The sending server only cares about the domain until the message arrives.

## The four steps

1. **Strip out the domain.** The sender takes everything after the `@`: the **fully qualified domain name** (FQDN) `example.com`.
2. **Ask DNS for the MX.** It queries the domain's nameservers for its **MX** records.
3. **DNS answers** with one or more mail hosts and their priorities.
4. **Send the message** to the address of the mail host the MX record named.

Programs do step 2 with a library call. In PHP, for example, it's `getmxrr(hostname, hosts, weights)`: give it the domain, and it fills in the list of mail **hosts** and their **weights** (priorities).

## Priorities

Lower numbers are **preferred**:

```
example.com.   IN  MX  10  mail1.example.com.
example.com.   IN  MX  20  mail2.example.com.
example.com.   IN  MX  20  mail3.example.com.
```

The sender tries `mail1` (10) first. If it can't connect, it tries `mail2` and `mail3` (both 20), picking between equal priorities at random to share the load. The numbers themselves don't matter, only their order: 10 and 20 work the same as 1 and 2.

## A real one: marshall.edu

From chapter 7:

```
$ dig mx marshall.edu +short
0 marshall-edu.mail.protection.outlook.com.
```

One MX, priority **0**. Marshall's mail is hosted by **Microsoft 365** (Exchange Online), whose filtering service is called Exchange Online Protection. That host name has **several A records**, so the sender then does step 4 with one of those addresses:

```
$ dig marshall-edu.mail.protection.outlook.com +short
52.101.42.14
52.101.10.12
...
```

The MX points at a **name**, and the name has several addresses. That's DNS round robin from chapter 7, doing load sharing for mail.

## When there's no MX

- **No MX, but an A record**: the rules (RFC 5321) say the sender should treat the domain's own A record as an **implicit MX** with priority 0.
- **No MX and no A**: the domain can't receive mail, so the message bounces.
- **Null MX**, `example.com. MX 0 .`: an explicit "this domain accepts **no** mail", so senders bounce at once instead of retrying for days.

In chapter 7, `whitehouse.gov` came back with **no MX records**, just its SOA. Whatever its mail setup is, it isn't published as MX records on that name.

Next, a check on finding the mail server.
