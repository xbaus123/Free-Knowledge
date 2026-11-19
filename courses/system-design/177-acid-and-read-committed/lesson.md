# Transactions, ACID, and Read Committed

*Chapter 7 · Transactions and Fault Tolerance.*

*Based on* Designing Data-Intensive Applications*, Chapter 7.*

*Based on* Designing Data-Intensive Applications*, Chapter 7.*

Many things can go wrong while your application changes data: the database crashes halfway through, the network drops, two clients write the same record at once, or a client reads data that's only half updated. A **transaction** groups several reads and writes into one logical unit that either **commits** entirely or **aborts** entirely, so the application doesn't have to handle every partial failure itself.

## ACID

| Letter | Meaning | What it really guarantees |
|---|---|---|
| **A**tomicity | All or nothing | If the transaction aborts (a crash, a constraint violation), every write in it is undone, so it's safe to retry. Better named *abortability*. |
| **C**onsistency | Invariants hold | Your application's rules (accounts balance, no double bookings) stay true. This depends on the *application*; the database only enforces the constraints you declare. |
| **I**solation | Concurrent transactions don't interfere | Ideally **serializable**: the result is as if the transactions ran one at a time. Most databases default to something weaker. |
| **D**urability | Committed data survives | It's written to disk (and the write-ahead log), or replicated, before the commit is confirmed. |

Isolation is where things get subtle. Serializability costs performance, so databases offer **weaker isolation levels**, each of which allows some **anomalies**. Bugs from these anomalies are rare, timing-dependent, and have cost real money.

## Read committed

The most basic level, and the default in PostgreSQL and Oracle. It prevents two anomalies:

- **Dirty reads**: seeing another transaction's uncommitted writes. If it later aborts, you acted on data that never existed.
- **Dirty writes**: overwriting another transaction's uncommitted write. Databases prevent these with row-level write locks held until commit.

Next, a short check on what you just read.
