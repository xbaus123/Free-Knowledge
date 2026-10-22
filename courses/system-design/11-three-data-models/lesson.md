# One Domain, Three Data Models

A small shop sells desk gear to five customers. You'll model it three ways (relational, document, and graph) and answer the same two questions in each:

1. **What has this customer bought?** `[(product_name, total_quantity), ...]`, sorted by product name.
2. **Who else bought something this customer bought?** The other customers' names, sorted, no duplicates.

Notice which model makes each question easy and which makes you fight it. That friction is the **impedance mismatch** from the last lesson.

## 1. Relational (SQL)

`conn` is a `sqlite3` connection. Answer each question with **one** SQL query: let `JOIN`, `GROUP BY`, and `DISTINCT` do the work.

```text
customers(id, name)
products(sku, name, price)
orders(id, customer_id → customers.id, placed_at)
order_items(order_id → orders.id, sku → products.sku, quantity)
```

```python
rows = conn.execute("SELECT name FROM customers WHERE id = ?", (1,)).fetchall()
```

For question 2, join `order_items` **to itself**: rows for my orders, matched on `sku` with rows for anyone else's orders.

## 2. Documents (MongoDB-style)

`db.customers` holds one document per customer, with orders and line items **embedded**. Product names are copied into each item (denormalized):

```json
{ "_id": 1, "name": "Ada",
  "orders": [ { "order_id": 101, "placed_at": "2024-03-01",
                "items": [ { "sku": "KB-1", "name": "Mechanical Keyboard", "price": 89, "quantity": 1 } ] } ] }
```

The store speaks a subset of MongoDB:

```python
db.customers.find_one({"name": "Ada"})                      # one document or None
db.customers.find({"age": {"$gt": 30}}, {"name": 1})         # filter, projection
db.customers.find({"orders.items.sku": "KB-1"})              # dotted paths search inside arrays
db.customers.aggregate([                                     # a pipeline of stages
    {"$match": {...}},
    {"$unwind": "$orders"},          # one document per array element
    {"$group": {"_id": "$field", "total": {"$sum": "$other.field"}}},
    {"$sort": {"_id": 1}},
])
```

Filter operators: `$eq $ne $gt $gte $lt $lte $in $nin $exists`, plus `$and` and `$or`. Stages: `$match $unwind $group $sort $project $limit`. `$group` accumulators: `$sum $first $push $addToSet`.

- Question 1: one `aggregate` call. Unwind the orders, then the items, then group by product name.
- Question 2: at most **two** queries, and let the store filter (`$in`, `$ne`) rather than fetching every customer. There's no join, so you look up the customer first.

## 3. Graph

`graph` is a property graph:

```text
(Customer {name}) -[:PLACED]-> (Order {placed_at}) -[:CONTAINS {quantity}]-> (Product {sku, name, price})
```

```python
graph.find("Customer", name="Ada")   # ["customer:1"]: vertex ids (an index lookup)
graph.props("product:KB-1")          # {"label": "Product", "sku": "KB-1", "name": ..., "price": ...}
graph.out("customer:1", "PLACED")    # [("order:101", {}), ...]: outgoing edges
graph.in_("product:KB-1", "CONTAINS")  # [("order:101", {"quantity": 1}), ...]: incoming edges
```

Look the customer up **once**, then walk edges. Question 2 is a path: customer → orders → products ← other orders ← other customers.

## Reflect

- Question 1 is a **one-to-many tree**: the document model answers it from a single document with no joins.
- Question 2 is **many-to-many**: easy as a SQL self-join and natural as a graph traversal, but the document model needs two round trips and an index on a nested field.
- The document model copied product names into every order. What happens when a product is renamed?
