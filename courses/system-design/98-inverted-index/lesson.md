# Why Search Needs an Inverted Index

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

*Based on* Designing Data-Intensive Applications*, Chapter 3.*

*Based on* Designing Data-Intensive Applications*, Chapter 3.*

Every index so far answers the same kind of question: *given a key, find the record*. A hash index finds `user:42`. A B-tree finds a key or a range of keys, like orders between Monday and Friday. Your SSTables did the same with sorted files.

Search asks the question the other way around: *given some words, find every document that contains them*, then rank those documents by how well they match, forgive the user's typos, and answer in a few milliseconds over billions of documents. A B-tree can't do that. These readings build the structure that can, the **inverted index**, and then looks inside Lucene and Elasticsearch, the engines that run most of the world's search boxes.

## Why B-trees aren't enough

Suppose a `products` table has a B-tree index on `title`, and a user searches for "wireless headphones":

```sql
SELECT * FROM products WHERE title LIKE '%wireless%' AND title LIKE '%headphones%';
```

The B-tree is sorted by the *whole* title, so it can find titles that *start with* "wireless", but not titles that contain it somewhere in the middle. The database scans every row. Even if it could find the matches, it would still have no idea which ones are *most relevant*, and it would miss "Wireless Headphone", "headphones (wireless)", and "wirless headphones" entirely.

Full-text search needs three things a B-tree doesn't give you:

1. **Lookup by word**, wherever the word appears.
2. **Relevance ranking**: the best matches first, not every match in insertion order.
3. **Fuzziness**: matching different forms and misspellings of a word.

## The inverted index

A **forward index** maps each document to its words, as the documents themselves do. An **inverted index** flips that around: it maps each **term** to the list of documents containing it, the term's **postings list**.

```text
d1: "The quick brown fox"           brown → d1, d2
d2: "A quick brown dog"       ⇒     dog   → d2, d3
d3: "Lazy dogs and a lazy dog"      fox   → d1
                                    lazy  → d3 (×2)
                                    quick → d1, d2
```

It has two parts:

- The **term dictionary**: every distinct term, kept sorted so it can be searched (and, as you'll see, searched fuzzily).
- The **postings**: for each term, the sorted ids of the documents that contain it, usually with the **term frequency** in each (how many times it appears) and the **positions** where it appears.

To answer `quick AND brown`, look up both postings lists and intersect them. Because both are sorted by document id, that's a linear merge, the same trick that let you merge sorted SSTables. `quick OR brown` is a union. Neither touches a document that doesn't contain at least one query term, so a query costs time proportional to the postings it reads, not to the size of the corpus.

Next, a short check on what you just read.
