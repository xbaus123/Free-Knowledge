"""A small bank in SQLite: a schema with constraints, indexes for the
queries that matter, and transfers that happen completely or not at all."""


# --- 1. Schema -------------------------------------------------------------


def create_schema(conn):
    conn.executescript(
        """
        CREATE TABLE users (
            id    INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            name  TEXT NOT NULL
        );
        CREATE TABLE accounts (
            id      INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users (id),
            balance INTEGER NOT NULL DEFAULT 0 CHECK (balance >= 0)
        );
        CREATE TABLE transfers (
            id           INTEGER PRIMARY KEY,
            from_account INTEGER NOT NULL REFERENCES accounts (id),
            to_account   INTEGER NOT NULL REFERENCES accounts (id),
            amount       INTEGER NOT NULL CHECK (amount > 0),
            created_at   TEXT NOT NULL
        );
        """
    )


# --- 2. Indexes ------------------------------------------------------------


def add_indexes(conn):
    conn.executescript(
        """
        CREATE INDEX accounts_by_user ON accounts (user_id);
        -- Finds a sender's transfers and returns them already sorted by time.
        CREATE INDEX transfers_by_sender ON transfers (from_account, created_at);
        """
    )


# --- 3. Transactions -------------------------------------------------------


def transfer(conn, from_id, to_id, amount, created_at):
    with conn:  # BEGIN; COMMIT at the end, or ROLLBACK if anything raises
        for account, change in ((from_id, -amount), (to_id, amount)):
            cur = conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (change, account))
            if cur.rowcount != 1:
                raise ValueError(f"no account {account}")
        conn.execute(
            "INSERT INTO transfers (from_account, to_account, amount, created_at) VALUES (?, ?, ?, ?)",
            (from_id, to_id, amount, created_at),
        )


# --- 4. Relational to document ---------------------------------------------


def user_document(conn, user_id):
    user = conn.execute("SELECT id, name, email FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        return None
    accounts = conn.execute("SELECT id, balance FROM accounts WHERE user_id = ? ORDER BY id", (user_id,)).fetchall()
    return {
        "id": user[0],
        "name": user[1],
        "email": user[2],
        "accounts": [{"id": a[0], "balance": a[1]} for a in accounts],
    }


# --- 5. B-trees ------------------------------------------------------------


def btree_height(rows, fanout):
    height, reach = 1, fanout
    while reach < rows:
        height += 1
        reach *= fanout
    return height
