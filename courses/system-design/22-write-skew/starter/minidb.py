"""minidb: a tiny in-memory SQL database with transactions. (Read-only.)

It behaves like PostgreSQL in the ways this lesson needs:

* Two isolation levels. "read committed" (the default) reads the latest
  committed data. "serializable" reads a snapshot taken when the
  transaction began, and refuses to commit if another transaction
  committed a write that would have changed what it read.
* Writes are private until commit, so nobody sees dirty data.
* SELECT ... FOR UPDATE locks the rows it returns until the transaction
  ends; another transaction locking (or updating) the same rows waits.

It understands this much SQL, with ? placeholders:

    SELECT * | col, col | count(*) FROM table [WHERE cond [AND cond ...]] [FOR UPDATE]
    INSERT INTO table (col, col) VALUES (?, ?)
    UPDATE table SET col = ? [, col = ?] WHERE cond [AND cond ...]
    DELETE FROM table WHERE cond [AND cond ...]

where each cond is `column op value`, op is one of = != <> < <= > >=, and
value is ? or a literal number or 'string'. Every table has an integer
`id` column, assigned on insert.

    db = Database()
    with db.transaction(isolation="serializable") as tx:
        rows = tx.execute("SELECT id, name FROM bays WHERE id = ?", (3,))
        # rows == [{"id": 3, "name": "Bay 3"}]

Leaving the `with` block commits; an exception rolls back.
"""

import itertools
import re
import threading

__all__ = ["Database", "SQLError", "LockTimeout", "SerializationFailure"]


class SQLError(Exception):
    """The statement isn't valid minidb SQL."""


class LockTimeout(Exception):
    """Waited too long for another transaction's lock."""


class SerializationFailure(Exception):
    """A serializable transaction can't commit because a concurrent
    transaction changed data it read. Retry it from the start."""


_COND = re.compile(r"^\s*(\w+)\s*(=|!=|<>|<=|>=|<|>)\s*(\?|-?\d+|'[^']*')\s*$")
_SELECT = re.compile(r"^\s*SELECT\s+(?P<cols>.+?)\s+FROM\s+(?P<table>\w+)(?:\s+WHERE\s+(?P<where>.+?))?(?P<lock>\s+FOR\s+UPDATE)?\s*;?\s*$", re.I | re.S)
_INSERT = re.compile(r"^\s*INSERT\s+INTO\s+(?P<table>\w+)\s*\((?P<cols>[^)]*)\)\s*VALUES\s*\((?P<vals>[^)]*)\)\s*;?\s*$", re.I | re.S)
_UPDATE = re.compile(r"^\s*UPDATE\s+(?P<table>\w+)\s+SET\s+(?P<sets>.+?)\s+WHERE\s+(?P<where>.+?)\s*;?\s*$", re.I | re.S)
_DELETE = re.compile(r"^\s*DELETE\s+FROM\s+(?P<table>\w+)\s+WHERE\s+(?P<where>.+?)\s*;?\s*$", re.I | re.S)
_OPS = {
    "=": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    "<>": lambda a, b: a != b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
}
ISOLATION_LEVELS = ("read committed", "serializable")


class _Params:
    def __init__(self, params):
        self.values = list(params)
        self.used = 0

    def take(self, token):
        if token == "?":
            if self.used >= len(self.values):
                raise SQLError("not enough parameters for the ? placeholders")
            self.used += 1
            return self.values[self.used - 1]
        if token.startswith("'"):
            return token[1:-1]
        return int(token)

    def done(self):
        if self.used != len(self.values):
            raise SQLError(f"{len(self.values)} parameters for {self.used} placeholders")


def _parse_where(text, params):
    conds = []
    for part in re.split(r"\s+AND\s+", text or "", flags=re.I) if text else []:
        m = _COND.match(part)
        if not m:
            raise SQLError(f"can't parse condition {part.strip()!r}: use `column op ?`, joined with AND")
        conds.append((m.group(1), m.group(2), params.take(m.group(3))))
    return conds


def _matches(row, conds):
    for col, op, value in conds:
        if col not in row:
            raise SQLError(f"no column {col!r}")
        if row[col] is None or not _OPS[op](row[col], value):
            return False
    return True


class Database:
    def __init__(self, lock_timeout=2.0):
        self._cv = threading.Condition()
        self._columns = {}
        # table -> {row id -> [(commit seq, row dict or None if deleted)]}
        self._versions = {}
        self._ids = itertools.count(1)
        self._tx_ids = itertools.count(1)
        self._seq = 0
        self._commits = []  # [(seq, [(table, row)])]: rows each commit wrote
        self._locks = {}  # (table, row id) -> transaction id
        self.lock_timeout = lock_timeout
        # Called with the transaction after every SELECT (tests use it to
        # force a worst-case interleaving).
        self.after_select = None
        self.stats = {"commits": 0, "serialization_failures": 0, "lock_waits": 0}
        # (transaction id, isolation level, statement) for every statement run.
        self.log = []

    def create_table(self, name, columns):
        self._columns[name] = ["id"] + [c for c in columns if c != "id"]
        self._versions[name] = {}

    def insert(self, table, **row):
        """Inserts a committed row directly (for setting up data)."""
        with self.transaction() as tx:
            cols = list(row)
            tx.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join('?' * len(cols))})", tuple(row.values()))

    def rows(self, table):
        """Every committed row in a table, by id."""
        with self._cv:
            return [dict(r) for r in self._visible(table, self._seq).values()]

    def transaction(self, isolation="read committed"):
        if isolation not in ISOLATION_LEVELS:
            raise ValueError(f"isolation must be one of {ISOLATION_LEVELS}")
        with self._cv:
            return Transaction(self, next(self._tx_ids), isolation, self._seq)

    def _visible(self, table, seq):
        if table not in self._versions:
            raise SQLError(f"no table {table!r}")
        out = {}
        for rid, versions in self._versions[table].items():
            row = None
            for s, r in versions:
                if s <= seq:
                    row = r
            if row is not None:
                out[rid] = row
        return out


class Transaction:
    def __init__(self, db, tx_id, isolation, snapshot):
        self.db = db
        self.id = tx_id
        self.isolation = isolation
        self.snapshot = snapshot
        self.writes = {}  # (table, row id) -> row dict, or None to delete
        self.reads = []  # (table, conds): what a serializable transaction saw
        self.locked = set()
        self.done = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        return False

    # --- statements ---

    def execute(self, sql, params=()):
        if self.done:
            raise SQLError("this transaction has already finished")
        self.db.log.append((self.id, self.isolation, " ".join(sql.split())))
        params = _Params(params)
        if m := _SELECT.match(sql):
            rows = self._select(m, params)
            if self.db.after_select:
                self.db.after_select(self)
            return rows
        if m := _INSERT.match(sql):
            return self._insert(m, params)
        if m := _UPDATE.match(sql):
            return self._update(m, params)
        if m := _DELETE.match(sql):
            return self._delete(m, params)
        raise SQLError("minidb understands SELECT, INSERT, UPDATE, and DELETE (see minidb.py)")

    def _rows(self, table):
        """What this transaction sees: a snapshot (serializable) or the
        latest committed data (read committed), plus its own writes."""
        seq = self.snapshot if self.isolation == "serializable" else self.db._seq
        rows = {rid: dict(r) for rid, r in self.db._visible(table, seq).items()}
        for (t, rid), row in self.writes.items():
            if t == table:
                if row is None:
                    rows.pop(rid, None)
                else:
                    rows[rid] = dict(row)
        return rows

    def _lock(self, table, rids):
        """Takes row locks, waiting for other transactions to finish."""
        for rid in sorted(rids):
            key = (table, rid)
            waited = False
            while self.db._locks.get(key, self.id) != self.id:
                if not waited:
                    self.db.stats["lock_waits"] += 1
                    waited = True
                if not self.db._cv.wait(self.db.lock_timeout):
                    self._finish()
                    raise LockTimeout(f"waited {self.db.lock_timeout} s for a lock on {table} row {rid}")
            self.db._locks[key] = self.id
            self.locked.add(key)

    def _select(self, m, params):
        table, cols = m.group("table"), m.group("cols").strip()
        conds = _parse_where(m.group("where"), params)
        params.done()
        with self.db._cv:
            matched = [r for r in self._rows(table).values() if _matches(r, conds)]
            if m.group("lock"):
                self._lock(table, [r["id"] for r in matched])
                if self.isolation == "read committed":
                    # Re-read after waiting: the rows may have changed.
                    matched = [r for r in self._rows(table).values() if _matches(r, conds)]
            if self.isolation == "serializable":
                self.reads.append((table, conds))
        matched.sort(key=lambda r: r["id"])
        if re.fullmatch(r"count\(\s*\*\s*\)", cols, re.I):
            return [{"count": len(matched)}]
        if cols == "*":
            return matched
        names = [c.strip() for c in cols.split(",")]
        for n in names:
            if n not in self.db._columns[table]:
                raise SQLError(f"no column {n!r} in {table}")
        return [{n: r[n] for n in names} for r in matched]

    def _insert(self, m, params):
        table = m.group("table")
        cols = [c.strip() for c in m.group("cols").split(",")]
        vals = [params.take(v.strip()) for v in m.group("vals").split(",")]
        params.done()
        if len(cols) != len(vals):
            raise SQLError("INSERT needs one value per column")
        if table not in self.db._columns:
            raise SQLError(f"no table {table!r}")
        unknown = set(cols) - set(self.db._columns[table]) | ({"id"} & set(cols))
        if unknown:
            raise SQLError(f"can't insert into column(s) {sorted(unknown)} of {table}")
        with self.db._cv:
            rid = next(self.db._ids)
        row = {c: None for c in self.db._columns[table]}
        row.update(zip(cols, vals), id=rid)
        self.writes[(table, rid)] = row
        return []

    def _update(self, m, params):
        table = m.group("table")
        sets = []
        for part in m.group("sets").split(","):
            col, _, val = part.partition("=")
            sets.append((col.strip(), params.take(val.strip())))
        conds = _parse_where(m.group("where"), params)
        params.done()
        with self.db._cv:
            rids = [r["id"] for r in self._rows(table).values() if _matches(r, conds)]
            self._lock(table, rids)  # writes lock their rows, like FOR UPDATE
            rows = self._rows(table)
            for rid in rids:
                if rid in rows:
                    row = rows[rid]
                    row.update(sets)
                    self.writes[(table, rid)] = row
        return []

    def _delete(self, m, params):
        table = m.group("table")
        conds = _parse_where(m.group("where"), params)
        params.done()
        with self.db._cv:
            rids = [r["id"] for r in self._rows(table).values() if _matches(r, conds)]
            self._lock(table, rids)
            for rid in rids:
                self.writes[(table, rid)] = None
        return []

    # --- ending ---

    def commit(self):
        if self.done:
            return
        db = self.db
        with db._cv:
            if self.isolation == "serializable":
                self._check_conflicts()
            db._seq += 1
            written = []
            for (table, rid), row in self.writes.items():
                before = db._visible(table, db._seq).get(rid)
                db._versions[table].setdefault(rid, []).append((db._seq, None if row is None else dict(row)))
                written.append((table, row if row is not None else before))
            db._commits.append((db._seq, written))
            db.stats["commits"] += 1
            self._finish()

    def _check_conflicts(self):
        db = self.db
        for seq, written in db._commits:
            if seq <= self.snapshot:
                continue
            for table, row in written:
                if row is None:
                    continue
                for t, conds in self.reads:
                    if t == table and _matches(row, conds):
                        self._fail(f"a concurrent transaction changed {table} rows this transaction read")
                if (table, row["id"]) in self.writes:
                    self._fail(f"a concurrent transaction updated the same {table} row")

    def _fail(self, why):
        self.db.stats["serialization_failures"] += 1
        self._finish()
        raise SerializationFailure(f"could not serialize access: {why}; retry the transaction")

    def rollback(self):
        if not self.done:
            with self.db._cv:
                self._finish()

    def _finish(self):
        """Releases locks and ends the transaction (call with the lock held)."""
        for key in self.locked:
            if self.db._locks.get(key) == self.id:
                del self.db._locks[key]
        self.locked.clear()
        self.done = True
        self.db._cv.notify_all()
