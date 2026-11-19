# Data Sovereignty and Residency

*Chapter 6 · Partitioning and Geography.*

## Data sovereignty and residency

- **Data residency**: *where* data is physically stored and processed.
- **Data sovereignty**: *whose laws* apply to it. Data stored in Frankfurt by an American company may still be subject to American legal demands, which is why some customers insist on providers headquartered locally.

The European Union's **GDPR** restricts transferring personal data outside the EU unless the destination offers equivalent protection. China, India, Russia, and others have localization laws of their own, and industries like healthcare and finance add more rules. The design consequences:

- **Partition by jurisdiction.** Give each user a home region in their jurisdiction, and keep their personal data there. Global services handle only pseudonymous ids.
- **Everything is data.** Logs, backups, analytics pipelines, search indexes, caches, error reports, and the support team's admin tools all copy data. A residency guarantee has to cover every one of them.
- **Fail closed.** If both EU regions are down, the router must refuse an EU user's request rather than quietly sending it to Virginia. A residency rule that a failover can violate isn't a rule. If you need regional failover, provision two regions *inside* the jurisdiction.
- **Encrypt with regional keys.** Keep encryption keys in a key management service in the same jurisdiction. Destroying a key makes every copy of the data unreadable, even in backups (**crypto-shredding**).

Next, a short check on what you just read.
