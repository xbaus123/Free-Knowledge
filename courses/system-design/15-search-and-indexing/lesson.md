# Search and Indexing: Inverted Indexes, Ranking, and Fuzzy Matching

*Based on* Designing Data-Intensive Applications*, Chapter 3.*

Every index so far answers the same kind of question: *given a key, find the record*. A hash index finds `user:42`. A B-tree finds a key or a range of keys, like orders between Monday and Friday. Your SSTables did the same with sorted files.

Search asks the question the other way around: *given some words, find every document that contains them*, then rank those documents by how well they match, forgive the user's typos, and answer in a few milliseconds over billions of documents. A B-tree can't do that. This lesson builds the structure that can, the **inverted index**, and then looks inside Lucene and Elasticsearch, the engines that run most of the world's search boxes.

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

### Making postings small and fast

Postings lists for common terms are huge (a term in half of a billion documents has 500 million entries), so engines work hard on them:

- **Delta encoding**: store the gaps between sorted doc ids (`1003, 1007, 1010` becomes `1003, 4, 3`). Small numbers then compress well with **variable-length integers** or **frame of reference** encoding, which packs a block of 128 gaps using just enough bits for the largest one.
- **Bitmaps**: very common terms can be stored as compressed bitmaps (**roaring bitmaps**), where AND and OR become fast bitwise operations.
- **Skip lists**: postings are stored in blocks with pointers that skip ahead. When intersecting a rare term (10 docs) with a common one (10 million), the engine jumps through the long list instead of reading it all.
- **Stopwords**: words like "the" and "of" appear in nearly every document and carry almost no meaning. Older engines drop them entirely. Modern ones often keep them, because compression makes them cheap and phrases like "to be or not to be" need them.

## Analysis: from text to terms

Before indexing, every piece of text goes through an **analyzer**, a pipeline that turns it into terms:

1. **Character filters**: strip HTML, normalize Unicode (`é` and `e` + combining accent are different bytes but the same letter).
2. **Tokenizer**: split into tokens at whitespace and punctuation. Languages like Chinese and Japanese don't put spaces between words, so they need dictionary-based tokenizers.
3. **Token filters**: lowercase, drop stopwords, **stem** words to a common root (`running`, `runs` → `run`) or **lemmatize** them with a dictionary (`better` → `good`), and add **synonyms** (`tv` ↔ `television`).

The rule that matters most: **the query goes through the same analyzer as the documents**. If documents are lowercased and stemmed but queries aren't, "Running" never matches anything. Analysis is a trade-off between **recall** (finding every relevant document) and **precision** (returning only relevant documents). Aggressive stemming finds more, but conflates words that differ in meaning, like "universe" and "university" (both stem to "univers" with the classic Porter stemmer).

## Ranking

A query for "raft consensus" may match a million documents. Users look at ten. **Relevance scoring** decides which ten. The intuitions, which go back to the 1970s:

- **Term frequency (TF)**: a document that mentions "raft" five times is probably more about Raft than one that mentions it once.
- **Inverse document frequency (IDF)**: a match on a rare term means more than a match on a common one. "raft" is rare and telling; "system" is everywhere and says little.
- **Length normalization**: one mention in a tweet means more than one mention in a 300-page book.

### BM25

**TF-IDF** multiplies the first two. **BM25** (Best Match 25), the default in Lucene, Elasticsearch, and most search engines since around 2016, refines all three. A document's score for a query is the sum, over the query's terms, of:

```text
                       tf × (k1 + 1)
score(t, d) = IDF(t) × ─────────────────────────────────────
                       tf + k1 × (1 − b + b × |d| / avgdl)

IDF(t) = ln(1 + (N − n + 0.5) / (n + 0.5))
```

where `tf` is how often term `t` appears in document `d`, `|d|` is the document's length in terms, `avgdl` is the average length, `N` is the number of documents, and `n` is how many contain `t`.

| Part | What it does |
|---|---|
| `IDF(t)` | Near 0 for a term in almost every document, large for a rare one |
| `k1` (usually 1.2) | **Saturation**: the tenth mention adds far less than the first. As `tf` grows, the fraction approaches `k1 + 1`, never more |
| `b` (usually 0.75) | How much to penalize long documents. `b = 0` ignores length; `b = 1` normalizes fully |

Saturation is BM25's key improvement over plain TF-IDF: with TF-IDF, a page that repeats a keyword 100 times scores 100 times higher, which is exactly what keyword-stuffing spammers exploit.

Ranking in production goes further. **Field boosts** make a match in the title count more than one in the body. **Function scores** blend in popularity, recency, or distance. And the top few hundred BM25 results are often **reranked** by a machine-learned model (**learning to rank**), which is too expensive to run on every match but cheap on a short list.

### Top-k without sorting everything

Scoring every match and sorting them all is wasteful when you want ten. Engines keep a **min-heap** of the best k so far, and algorithms like **WAND** and **block-max WAND** go further: each term knows the highest score it can possibly contribute, so the engine skips whole blocks of documents that can't beat the current tenth-best score.

## Phrases and positions

"New York" shouldn't match a document about a *new* office in *York*. **Phrase queries** need to know *where* each term appears, so postings store **positions**: `new → d7: [4, 19]`, `york → d7: [5]`. A document matches the phrase if there's a position `p` with `new` at `p` and `york` at `p + 1`.

Removed stopwords should still leave a gap. In "state of the art", "art" is three positions after "state". If the analyzer renumbered positions after dropping stopwords, "state of the art" would match a document that says "state art". A **slop** parameter relaxes the match to allow terms a few positions apart, for proximity search.

## Fuzzy matching

About 10 to 15% of search queries contain a typo. **Edit distance** measures how far apart two strings are. The **Levenshtein distance** counts the fewest single-character insertions, deletions, and substitutions that turn one into the other: `kitten → sitten → sittin → sitting` is 3. The **Damerau-Levenshtein** variant also counts swapping two adjacent letters as one edit, which suits human typos (`teh` for `the`). Elasticsearch counts transpositions by default, and its `fuzziness: AUTO` allows 0 edits for terms of 1 or 2 characters, 1 edit for 3 to 5, and 2 beyond that.

Comparing the query term against every term in the dictionary is too slow for a dictionary of millions. Lucene builds a **Levenshtein automaton**: a finite state machine that accepts exactly the strings within distance k of the query term. It then walks the automaton and the term dictionary together, visiting only the branches that can still match. DDIA points out that this works because Lucene's term dictionary is itself stored as a **finite state transducer (FST)**, a compressed trie-like automaton that shares common prefixes *and* suffixes between terms, so it fits in memory.

Other tools for inexact matching:

- **Prefix queries and autocomplete**: a sorted term dictionary finds every term starting with `elas` with one seek. For search-as-you-type, index **edge n-grams** (`e, el, ela, elas, …`) so prefixes become ordinary terms.
- **N-grams**: index every 3-character substring (`hea, ead, adp, …`) to support infix matches and to find candidate spellings.
- **Phonetic** filters like Soundex and Metaphone match words that *sound* alike (`Smith`, `Smyth`).
- **"Did you mean?"**: suggest dictionary terms close to an unknown query term, preferring the most common ones.

## Inside Lucene

Lucene is the Java library inside Elasticsearch, OpenSearch, and Solr. Its storage design should look familiar from lesson 14: it's a **log-structured** engine, and its files are **immutable segments**, much like SSTables.

- New documents go into an **in-memory buffer**.
- Every second or so, a **refresh** writes the buffer out as a new, small **segment**, a complete mini inverted index, and makes it searchable. That's why Elasticsearch is **near-real-time**: a document you just indexed may not appear in search for up to the refresh interval.
- Segments are opened but not yet fsynced to disk. For durability, Elasticsearch also appends every operation to a **translog**, a write-ahead log. A periodic **flush** fsyncs the segments and truncates the translog.
- A search runs against **every segment** and merges the results. Many small segments make searches slow, so a background **merge policy** combines segments into bigger ones, like compaction.
- Segments are never modified, so a **delete** only sets a bit in the segment's **live-docs bitmap**, a tombstone. An **update** is a delete plus an add. The deleted document's space is reclaimed when its segment is merged.

Immutability has the same benefits it had for SSTables: segments can be cached aggressively by the operating system, read without locks, and compressed heavily. The cost is write amplification from merging, and a refresh interval that trades freshness against indexing throughput.

An inverted index answers "which documents contain this term?" but is terrible at "what is document 7's price?", which sorting and aggregations need for every match. So Lucene also stores **doc values**: a **column-oriented** copy of chosen fields, one column per field, the column storage you met in lesson 12.

## Search at scale: Elasticsearch

An Elasticsearch **index** is split into **shards**, each a complete Lucene index, spread across a cluster of nodes:

- The number of **primary shards** is fixed when the index is created. A document goes to shard `hash(_id) % primaries`. This is partitioning with a fixed number of partitions (lesson 22): to grow, you add nodes and move whole shards, never re-hash documents. Changing the shard count means reindexing.
- Each primary has **replica shards** on other nodes. Replicas give failover *and* read capacity: any copy of a shard can answer a search. Search is **read-heavy** (often a hundred searches for each update), so read throughput scales by adding replicas.

A search is a **scatter-gather** in two phases, **query then fetch**:

1. **Query**: the coordinating node sends the query to one copy of every shard. Each shard finds its own top k and returns only ids and scores.
2. **Fetch**: the coordinator merges those lists into the global top k, then fetches the full documents for just those k from the shards that hold them.

Scatter-gather has consequences:

- **Tail latency**: a search is as slow as its slowest shard. With 50 shards, even a 1% chance of a slow shard makes 40% of searches slow (lesson 1's tail latency amplification). Engines hedge by sending duplicate requests to replicas, and set timeouts that return partial results.
- **Deep pagination is expensive**: page 1,000 of 10 results means every shard returns its top 10,010, and the coordinator sorts them all. Use a cursor (`search_after`) instead of `from` and `size`.
- **Distributed scoring is approximate**: each shard computes IDF from its own documents only, so with few documents per shard, scores can differ slightly depending on where a document landed.

### Search is derived data

A search index is almost never the **system of record**. The source of truth stays in a database. The index is a **derived** view, rebuilt from that source whenever its analyzers or mappings change. Keeping it in sync reliably is a classic problem: dual-writing from the application loses updates whenever the index is down. Lesson 35 fixes that with change data capture.

### Beyond keywords

Keyword search fails when users and documents use different words for the same idea ("cheap flights" vs. "low-cost airfare"). **Vector search** embeds documents and queries as points in a high-dimensional space, using a machine-learning model, and finds the **nearest neighbors** to the query. Exact nearest-neighbor search in hundreds of dimensions is too slow, so engines use **approximate** indexes like **HNSW** (hierarchical navigable small-world graphs). Many systems now run **hybrid search**: BM25 and vector results, merged into one ranking. **Geospatial** search ("restaurants within 2 km") uses yet another family of indexes, such as R-trees and geohashes, which turn two-dimensional proximity into something an index can look up.

## Your task

`solution.py` holds a small search engine. `analyze(text)` is done: it returns `(position, term)` pairs, lowercased, with stopwords removed but still counted as positions. Each `Index` keeps:

- `self.postings`: `{term: {doc_id: [positions]}}`, positions in increasing order.
- `self.doc_len`: `{doc_id: number of terms}` (stopwords don't count).

Add any other attributes you need.

### 1. Indexing

- `add(doc_id, text)` analyzes the text and records every term's positions. Adding a `doc_id` that's already indexed **replaces** the old version.
- `delete(doc_id)` removes the document from every postings list, and removes terms left with no documents. Deleting an unknown id does nothing.

### 2. Ranking

`search(query, k=10, fuzziness=0)` returns the top `k` `(doc_id, score)` pairs, highest score first, ties broken by smaller `doc_id`. Score with BM25 as above, using `self.k1`, `self.b`, and the given `idf(term)`. Score each **distinct** query term once. An empty index or no matches gives `[]`.

Only read the postings of the query's terms. A test runs 1,000 searches over 20,000 documents and fails if you loop over every document.

### 3. Phrases

`phrase(query)` returns the sorted ids of documents containing the query's terms at the same relative positions as in the query. Remember that a term can appear several times in a document, so check every place the phrase could start.

### 4. Fuzzy matching

- `levenshtein(a, b)` at the bottom of the file: the edit distance, by dynamic programming. `dist[i][j]` is the distance between the first `i` characters of `a` and the first `j` of `b`, and each cell is the cheapest of a deletion, an insertion, or a substitution (free if the characters match). You only need to keep the previous row.
- `fuzzy_terms(term, max_edits)`: the set of indexed terms within `max_edits` of `term`. Two strings whose lengths differ by more than `max_edits` can't be within it, so skip them without computing the distance.
- `suggest(word, max_edits=2, limit=5)`: the lowercased word's fuzzy terms, sorted by distance, then by how many documents contain them (most first), then alphabetically, cut to `limit`.
- With `fuzziness > 0`, `search` replaces each query term with all of its fuzzy terms.

Experiment in the **Scratchpad**:

```python
from solution import Index

ix = Index()
ix.add("a", "Designing data-intensive applications")
ix.add("b", "Intensive care for data")
print(ix.search("data intensive"), ix.phrase("data intensive"))
print(ix.suggest("aplications"))
```

## Think about it

- Your index updates postings in place. Lucene never does: it writes new immutable segments and merges them later. What would in-place updates cost on disk, and what does immutability cost instead?
- A shard computes IDF from its own documents. Index 10 documents mentioning "raft" all into one shard of five. What happens to their scores compared with documents in the other shards?
- Should a product search for "iphone 15 case" rank by BM25 alone? What other signals would you blend in, and where in the pipeline?

## Key terms

| Term | Meaning |
|---|---|
| Inverted index | A map from each term to the documents that contain it |
| Postings list | One term's documents, with frequencies and positions |
| Term dictionary | The sorted set of every indexed term |
| Analyzer | The pipeline that turns text into terms: tokenize, normalize, filter |
| Stemming | Reducing words to a common root, like `running` → `run` |
| Precision / recall | How many results are relevant / how many relevant documents were found |
| TF-IDF / BM25 | Relevance scores from term frequency, rarity, and document length |
| Phrase query | Terms that must appear next to each other, in order |
| Levenshtein distance | The fewest insertions, deletions, and substitutions between two strings |
| Levenshtein automaton | A state machine accepting every string within k edits of a term |
| Segment | An immutable mini-index; Lucene's equivalent of an SSTable |
| Refresh | Writing buffered documents into a new searchable segment |
| Doc values | A column-oriented copy of fields, for sorting and aggregations |
| Query then fetch | Gather each shard's top ids and scores, then fetch only the winners |
