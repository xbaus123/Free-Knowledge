# DNS Tricks

*Chapter 7 · DNS.*

DNS answers "where is this name?" Since the server gets to choose the answer, it can do more than look up a fixed address.

## Round robin

Give a name **several A records**, and the server rotates their order on each reply. Clients usually connect to the first address, so the load spreads across the servers.

The `marshall.edu` mail host is a real example: one name, four addresses:

```
Name:    marshall-edu.mail.protection.outlook.com
Address: 52.101.42.14
Address: 52.101.10.12
Address: 52.101.9.17
Address: 52.101.8.34
```

An alias works the same way: a CNAME can point at a name that has many addresses. The limit: DNS doesn't know whether a server is **down**, and caches keep handing out its address until the TTL expires. Real load balancers check health; plain round robin doesn't.

## Split configurations (split horizon)

The server gives **different answers depending on who's asking**:

- Inside the company, `intranet.example.com` → `10.0.5.20`, a private address.
- From the Internet, the same name → nothing, or a public address.

Internal names and private addresses stay off the public Internet, and staff use the same name in both places. The cost is running two **views** of the zone and keeping them consistent.

## DNS and BGP for anycast

Remember from chapter 6 that BGP spreads route announcements, and routers pick the best path. With **anycast**, **many servers in different places announce the same IP prefix** with BGP. Each user's packets go to whichever copy is **nearest** in routing terms.

- The **root servers** work this way: 13 identities, but hundreds of physical servers around the world.
- **Public resolvers** too: `1.1.1.1` and `8.8.8.8` are one address each, answered by sites on every continent.
- It's a strong **DDoS defense**: an attack is split across every site, instead of drowning one.

UDP suits anycast well: one question, one answer, so it doesn't matter if the next packet lands at a different site.

## Geo-DNS

Related trick: an authoritative server looks at where the **resolver** asking is located and returns the address of a nearby data center. Content delivery networks (CDNs) do this, so a user in Paris and one in Tokyo get different addresses for the same name.

Next, a check on the tricks.
