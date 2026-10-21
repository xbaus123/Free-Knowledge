"""A small bank in SQLite: a schema with constraints, indexes for the
queries that matter, and transfers that happen completely or not at all.

Every function gets conn, a sqlite3 connection with foreign keys turned on.
"""


# --- 1. Schema -------------------------------------------------------------


def create_schema(conn):
    """Create users, accounts, and transfers. Let the database enforce the
    rules: the lesson lists every column and constraint."""
    conn.executescript(
        """
        CREATE TABLE users (
            id    INTEGER PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            name  TEXT NOT NULL
        );
        CREATE TABLE accounts (
            id      INTEGER PRIMARY KEY,
            user_id INTEGER,
            balance INTEGER
        );
        -- TODO: transfers
        """
    )


# --- 2. Indexes ------------------------------------------------------------


def add_indexes(conn):
    """Add indexes so these queries never scan a whole table:

    SELECT * FROM accounts WHERE user_id = ?
    SELECT * FROM transfers WHERE from_account = ? ORDER BY created_at DESC LIMIT 10
    """


# --- 3. Transactions -------------------------------------------------------


def transfer(conn, from_id, to_id, amount, created_at):
    """Move amount between accounts and record it in transfers, all or
    nothing. Raise ValueError for an account that doesn't exist."""
    conn.execute("UPDATE accounts SET balance = balance - ? WHERE id = ?", (amount, from_id))
    conn.commit()
    conn.execute("UPDATE accounts SET balance = balance + ? WHERE id = ?", (amount, to_id))
    conn.commit()
    conn.execute(
        "INSERT INTO transfers (from_account, to_account, amount, created_at) VALUES (?, ?, ?, ?)",
        (from_id, to_id, amount, created_at),
    )
    conn.commit()


# --- 4. Relational to document ---------------------------------------------


def user_document(conn, user_id):
    """Return the user as one nested document, or None:

    {"id": 1, "name": "Ada", "email": "ada@example.com",
     "accounts": [{"id": 10, "balance": 500}, ...]}    accounts in id order
    """
    return None


# --- 5. B-trees ------------------------------------------------------------


def btree_height(rows, fanout):
    """How many levels a B-tree needs so that fanout ** levels >= rows
    (at least 1)."""
    raise NotImplementedError
