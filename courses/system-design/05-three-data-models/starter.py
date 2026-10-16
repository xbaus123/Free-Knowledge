"""One shop, three data models. Answer the same two questions in each.

The tests call each function with a database loaded with the same shop
data, modeled three ways (see the lesson for the shapes and APIs):

  conn  - a sqlite3 connection (relational). Use ONE SQL query per function.
  db    - a document store with a MongoDB-style API (db.customers).
  graph - a property graph of Customer, Order, and Product vertices.
"""


# --- Question 1: what has this customer bought? ---------------------------
# Return [(product_name, total_quantity), ...] sorted by product name.
# A customer who doesn't exist has bought nothing: return [].


def products_sql(conn, customer):
    rows = conn.execute(
        """
        SELECT ...
        """,
        (customer,),
    ).fetchall()
    return [tuple(r) for r in rows]


def products_mongo(db, customer):
    # One aggregation pipeline: $match, $unwind, $group, $sort.
    docs = db.customers.aggregate([
        {"$match": {"name": customer}},
        # TODO
    ])
    return [(d["_id"], d["quantity"]) for d in docs]


def products_graph(graph, customer):
    # Find the customer vertex, then follow PLACED and CONTAINS edges.
    return []


# --- Question 2: who else bought something this customer bought? ---------
# Return the other customers' names, sorted, without duplicates.


def also_bought_sql(conn, customer):
    return []


def also_bought_mongo(db, customer):
    # At most two queries. Let the store do the filtering.
    return []


def also_bought_graph(graph, customer):
    return []
