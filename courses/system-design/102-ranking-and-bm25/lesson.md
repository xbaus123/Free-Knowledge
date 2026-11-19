# Ranking and BM25

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

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

Next, a short check on what you just read.
