import copy
import sqlite3
import unittest

import solution

# --- The shop -------------------------------------------------------------

CUSTOMERS = {1: "Ada", 2: "Grace", 3: "Linus", 4: "Margaret", 5: "Ken"}
PRODUCTS = {
    "KB-1": ("Mechanical Keyboard", 89),
    "MS-1": ("Wireless Mouse", 25),
    "MN-1": ("4K Monitor", 320),
    "HD-1": ("USB-C Hub", 45),
    "CH-1": ("Desk Chair", 210),
    "LS-1": ("Laptop Stand", 40),
}
# order id -> (customer id, date, [(sku, quantity)])
ORDERS = {
    101: (1, "2024-03-01", [("KB-1", 1), ("MS-1", 2)]),
    102: (2, "2024-03-02", [("MN-1", 2), ("HD-1", 1)]),
    103: (3, "2024-03-02", [("KB-1", 1), ("CH-1", 1)]),
    104: (1, "2024-03-05", [("MN-1", 1), ("MS-1", 1)]),
    105: (4, "2024-03-07", [("LS-1", 1), ("HD-1", 2)]),
    106: (5, "2024-03-09", [("CH-1", 1)]),
}

PRODUCTS_BOUGHT = {
    "Ada": [("4K Monitor", 1), ("Mechanical Keyboard", 1), ("Wireless Mouse", 3)],
    "Grace": [("4K Monitor", 2), ("USB-C Hub", 1)],
    "Ken": [("Desk Chair", 1)],
    "Nobody": [],
}
ALSO_BOUGHT = {
    "Ada": ["Grace", "Linus"],
    "Margaret": ["Grace"],
    "Ken": ["Linus"],
    "Grace": ["Ada", "Margaret"],
    "Nobody": [],
}

# --- Relational: sqlite3 ----------------------------------------------------


class CountingConnection:
    """A sqlite3 connection that counts queries."""

    def __init__(self, conn):
        self._conn = conn
        self.queries = 0

    def execute(self, sql, params=()):
        self.queries += 1
        return self._conn.execute(sql, params)


def relational():
    conn = sqlite3.connect(":memory:")
    conn.executescript(
        """
        CREATE TABLE customers (id INTEGER PRIMARY KEY, name TEXT NOT NULL);
        CREATE TABLE products (sku TEXT PRIMARY KEY, name TEXT NOT NULL, price INTEGER NOT NULL);
        CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER NOT NULL REFERENCES customers(id), placed_at TEXT NOT NULL);
        CREATE TABLE order_items (order_id INTEGER NOT NULL REFERENCES orders(id), sku TEXT NOT NULL REFERENCES products(sku), quantity INTEGER NOT NULL);
        """
    )
    conn.executemany("INSERT INTO customers VALUES (?, ?)", CUSTOMERS.items())
    conn.executemany("INSERT INTO products VALUES (?, ?, ?)", [(sku, n, p) for sku, (n, p) in PRODUCTS.items()])
    for oid, (cid, date, items) in ORDERS.items():
        conn.execute("INSERT INTO orders VALUES (?, ?, ?)", (oid, cid, date))
        conn.executemany("INSERT INTO order_items VALUES (?, ?, ?)", [(oid, sku, q) for sku, q in items])
    return CountingConnection(conn)


# --- Documents: a tiny MongoDB-style store -----------------------------------


class UnsupportedQuery(Exception):
    pass


def _get(doc, path):
    """The value at a dotted path (no array traversal), or None."""
    for part in path.split("."):
        if not isinstance(doc, dict) or part not in doc:
            return None
        doc = doc[part]
    return doc


def _values(doc, path):
    """Every value a query path can match, traversing arrays like MongoDB."""
    vals = [doc]
    for part in path.split("."):
        nxt = []
        for v in vals:
            items = v if isinstance(v, list) else [v]
            for item in items:
                if isinstance(item, dict) and part in item:
                    nxt.append(item[part])
        vals = nxt
    out = []
    for v in vals:
        if isinstance(v, list):
            out.extend(v)
        out.append(v)
    return out


_COMPARE = {
    "$eq": lambda vs, x: any(v == x for v in vs),
    "$ne": lambda vs, x: all(v != x for v in vs),
    "$gt": lambda vs, x: any(v is not None and v > x for v in vs),
    "$gte": lambda vs, x: any(v is not None and v >= x for v in vs),
    "$lt": lambda vs, x: any(v is not None and v < x for v in vs),
    "$lte": lambda vs, x: any(v is not None and v <= x for v in vs),
    "$in": lambda vs, xs: any(v in xs for v in vs),
    "$nin": lambda vs, xs: all(v not in xs for v in vs),
    "$exists": lambda vs, x: bool(vs) == bool(x),
}


def _matches(doc, flt):
    for key, cond in (flt or {}).items():
        if key == "$and":
            if not all(_matches(doc, f) for f in cond):
                return False
            continue
        if key == "$or":
            if not any(_matches(doc, f) for f in cond):
                return False
            continue
        if key.startswith("$"):
            raise UnsupportedQuery(f"this store doesn't support the {key} operator")
        vals = _values(doc, key)
        if isinstance(cond, dict) and cond and all(k.startswith("$") for k in cond):
            for op, arg in cond.items():
                if op not in _COMPARE:
                    raise UnsupportedQuery(f"this store doesn't support {op} (try {', '.join(_COMPARE)})")
                if op in ("$in", "$nin") and not isinstance(arg, (list, tuple, set)):
                    raise UnsupportedQuery(f"{op} needs a list")
                if not _COMPARE[op](vals, arg):
                    return False
        elif not any(v == cond for v in vals):
            return False
    return True


def _project(doc, projection):
    if not projection:
        return doc
    include = {k for k, v in projection.items() if v and k != "_id"}
    if include:
        out = {k: copy.deepcopy(doc[k]) for k in include if k in doc}
        if projection.get("_id", 1):
            out["_id"] = doc["_id"]
        return out
    return {k: v for k, v in doc.items() if projection.get(k, 1)}


def _expr(doc, e):
    return _get(doc, e[1:]) if isinstance(e, str) and e.startswith("$") else e


def _set(doc, path, value):
    parts = path.split(".")
    for part in parts[:-1]:
        doc = doc[part]
    doc[parts[-1]] = value


class Collection:
    def __init__(self, docs, log):
        self._docs = docs
        self._log = log

    def _record(self, method, results):
        self._log.append((method, len(results)))
        return results

    def find(self, filter=None, projection=None):
        out = [_project(copy.deepcopy(d), projection) for d in self._docs if _matches(d, filter)]
        return self._record("find", out)

    def find_one(self, filter=None, projection=None):
        for d in self._docs:
            if _matches(d, filter):
                self._record("find_one", [d])
                return _project(copy.deepcopy(d), projection)
        self._record("find_one", [])
        return None

    def aggregate(self, pipeline):
        docs = copy.deepcopy(self._docs)
        for stage in pipeline:
            if len(stage) != 1:
                raise UnsupportedQuery(f"each pipeline stage needs exactly one operator: {stage}")
            (op, arg), = stage.items()
            if op == "$match":
                docs = [d for d in docs if _matches(d, arg)]
            elif op == "$unwind":
                path = arg[1:] if isinstance(arg, str) and arg.startswith("$") else None
                if not path:
                    raise UnsupportedQuery('$unwind takes a field path like "$orders"')
                out = []
                for d in docs:
                    for item in _get(d, path) or []:
                        nd = copy.deepcopy(d)
                        _set(nd, path, item)
                        out.append(nd)
                docs = out
            elif op == "$group":
                groups = {}
                for d in docs:
                    key = _expr(d, arg["_id"])
                    hkey = repr(key)
                    g = groups.setdefault(hkey, {"_id": key})
                    for field, acc in arg.items():
                        if field == "_id":
                            continue
                        (aop, aexpr), = acc.items()
                        v = _expr(d, aexpr)
                        if aop == "$sum":
                            g[field] = g.get(field, 0) + (v or 0)
                        elif aop == "$first":
                            g.setdefault(field, v)
                        elif aop == "$push":
                            g.setdefault(field, []).append(v)
                        elif aop == "$addToSet":
                            s = g.setdefault(field, [])
                            if v not in s:
                                s.append(v)
                        else:
                            raise UnsupportedQuery(f"$group supports $sum, $first, $push, $addToSet (got {aop})")
                docs = list(groups.values())
            elif op == "$sort":
                for field, direction in reversed(list(arg.items())):
                    docs.sort(key=lambda d: (_get(d, field) is None, _get(d, field)), reverse=direction < 0)
            elif op == "$project":
                out = []
                for d in docs:
                    nd = {"_id": d.get("_id")} if arg.get("_id", 1) else {}
                    for field, spec in arg.items():
                        if field == "_id":
                            continue
                        if spec in (1, True):
                            nd[field] = _get(d, field)
                        elif isinstance(spec, str):
                            nd[field] = _expr(d, spec)
                    out.append(nd)
                docs = out
            elif op == "$limit":
                docs = docs[:arg]
            else:
                raise UnsupportedQuery(f"this store supports $match, $unwind, $group, $sort, $project, and $limit (not {op})")
        return self._record("aggregate", docs)


class DocumentStore:
    def __init__(self):
        self.log = []
        docs = []
        for cid, name in CUSTOMERS.items():
            orders = []
            for oid, (owner, date, items) in ORDERS.items():
                if owner == cid:
                    orders.append({
                        "order_id": oid,
                        "placed_at": date,
                        "items": [{"sku": s, "name": PRODUCTS[s][0], "price": PRODUCTS[s][1], "quantity": q} for s, q in items],
                    })
            docs.append({"_id": cid, "name": name, "orders": orders})
        self.customers = Collection(docs, self.log)


# --- Graph: a tiny property graph --------------------------------------------


class Graph:
    """Vertices have a label and properties; edges have a label and properties."""

    def __init__(self):
        self._props = {}
        self._out = {}
        self._in = {}
        self.finds = 0
        for cid, name in CUSTOMERS.items():
            self._vertex(f"customer:{cid}", "Customer", name=name)
        for sku, (name, price) in PRODUCTS.items():
            self._vertex(f"product:{sku}", "Product", sku=sku, name=name, price=price)
        for oid, (cid, date, items) in ORDERS.items():
            self._vertex(f"order:{oid}", "Order", placed_at=date)
            self._edge(f"customer:{cid}", "PLACED", f"order:{oid}")
            for sku, q in items:
                self._edge(f"order:{oid}", "CONTAINS", f"product:{sku}", quantity=q)

    def _vertex(self, vid, label, **props):
        self._props[vid] = dict(props, label=label)

    def _edge(self, a, label, b, **props):
        self._out.setdefault((a, label), []).append((b, props))
        self._in.setdefault((b, label), []).append((a, props))

    def find(self, label, **props):
        """Vertex ids with this label and these properties (an index lookup)."""
        self.finds += 1
        return sorted(v for v, p in self._props.items() if p["label"] == label and all(p.get(k) == x for k, x in props.items()))

    def props(self, vid):
        return dict(self._props[vid])

    def out(self, vid, label):
        """Outgoing edges with this label: [(neighbor id, edge properties)]."""
        return [(v, dict(p)) for v, p in self._out.get((vid, label), [])]

    def in_(self, vid, label):
        """Incoming edges with this label: [(neighbor id, edge properties)]."""
        return [(v, dict(p)) for v, p in self._in.get((vid, label), [])]


# --- Tests ------------------------------------------------------------------


class RelationalTest(unittest.TestCase):
    def test_products(self):
        """SQL: what each customer bought, in one query"""
        for name, want in PRODUCTS_BOUGHT.items():
            conn = relational()
            self.assertEqual(solution.products_sql(conn, name), want, f"customer {name}")
            self.assertEqual(conn.queries, 1, "answer with a single SQL query: let JOIN and GROUP BY do the work")

    def test_also_bought(self):
        """SQL: who else bought the same products, in one query"""
        for name, want in ALSO_BOUGHT.items():
            conn = relational()
            self.assertEqual(solution.also_bought_sql(conn, name), want, f"customer {name}")
            self.assertEqual(conn.queries, 1, "answer with a single SQL query (join order_items to itself)")


class DocumentTest(unittest.TestCase):
    def test_products(self):
        """Documents: what each customer bought, in one aggregation pipeline"""
        for name, want in PRODUCTS_BOUGHT.items():
            db = DocumentStore()
            self.assertEqual(solution.products_mongo(db, name), want, f"customer {name}")
            self.assertEqual([m for m, _ in db.log], ["aggregate"], "use a single db.customers.aggregate([...]) call")

    def test_also_bought(self):
        """Documents: who else bought the same products, filtered by the store"""
        for name, want in ALSO_BOUGHT.items():
            db = DocumentStore()
            self.assertEqual(solution.also_bought_mongo(db, name), want, f"customer {name}")
            self.assertLessEqual(len(db.log), 2, "use at most two queries")
            returned = sum(n for _, n in db.log)
            self.assertLessEqual(returned, len(want) + 1, "filter in the query ($in, $ne) instead of fetching every customer")


class GraphTest(unittest.TestCase):
    def test_products(self):
        """Graph: what each customer bought, by traversing edges"""
        for name, want in PRODUCTS_BOUGHT.items():
            g = Graph()
            self.assertEqual(solution.products_graph(g, name), want, f"customer {name}")
            self.assertLessEqual(g.finds, 1, "look up the customer once, then traverse")

    def test_also_bought(self):
        """Graph: who else bought the same products, by traversing edges"""
        for name, want in ALSO_BOUGHT.items():
            g = Graph()
            self.assertEqual(solution.also_bought_graph(g, name), want, f"customer {name}")
            self.assertLessEqual(g.finds, 1, "look up the customer once, then traverse")


if __name__ == "__main__":
    unittest.main()
