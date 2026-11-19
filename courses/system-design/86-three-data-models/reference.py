"""Reference solution: the same two questions in three data models."""


def products_sql(conn, customer):
    rows = conn.execute(
        """
        SELECT p.name, SUM(oi.quantity)
        FROM customers c
        JOIN orders o       ON o.customer_id = c.id
        JOIN order_items oi ON oi.order_id = o.id
        JOIN products p     ON p.sku = oi.sku
        WHERE c.name = ?
        GROUP BY p.name
        ORDER BY p.name
        """,
        (customer,),
    ).fetchall()
    return [tuple(r) for r in rows]


def products_mongo(db, customer):
    docs = db.customers.aggregate([
        {"$match": {"name": customer}},
        {"$unwind": "$orders"},
        {"$unwind": "$orders.items"},
        {"$group": {"_id": "$orders.items.name", "quantity": {"$sum": "$orders.items.quantity"}}},
        {"$sort": {"_id": 1}},
    ])
    return [(d["_id"], d["quantity"]) for d in docs]


def products_graph(graph, customer):
    totals = {}
    for c in graph.find("Customer", name=customer):
        for order, _ in graph.out(c, "PLACED"):
            for product, edge in graph.out(order, "CONTAINS"):
                name = graph.props(product)["name"]
                totals[name] = totals.get(name, 0) + edge["quantity"]
    return sorted(totals.items())


def also_bought_sql(conn, customer):
    rows = conn.execute(
        """
        SELECT DISTINCT other.name
        FROM customers me
        JOIN orders mo        ON mo.customer_id = me.id
        JOIN order_items mi   ON mi.order_id = mo.id
        JOIN order_items oi   ON oi.sku = mi.sku
        JOIN orders oo        ON oo.id = oi.order_id
        JOIN customers other  ON other.id = oo.customer_id
        WHERE me.name = ? AND other.id <> me.id
        ORDER BY other.name
        """,
        (customer,),
    ).fetchall()
    return [r[0] for r in rows]


def also_bought_mongo(db, customer):
    me = db.customers.find_one({"name": customer})
    if me is None:
        return []
    skus = sorted({item["sku"] for order in me["orders"] for item in order["items"]})
    others = db.customers.find({"orders.items.sku": {"$in": skus}, "name": {"$ne": customer}}, {"name": 1})
    return sorted({d["name"] for d in others})


def also_bought_graph(graph, customer):
    names = set()
    for me in graph.find("Customer", name=customer):
        for order, _ in graph.out(me, "PLACED"):
            for product, _ in graph.out(order, "CONTAINS"):
                for other_order, _ in graph.in_(product, "CONTAINS"):
                    for other, _ in graph.in_(other_order, "PLACED"):
                        if other != me:
                            names.add(graph.props(other)["name"])
    return sorted(names)
