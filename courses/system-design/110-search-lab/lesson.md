# Search and Indexing: Inverted Indexes, Ranking, and Fuzzy Matching

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

Build a small search engine from the last six readings: an inverted index with positions, BM25 ranking, phrase queries, and fuzzy matching.

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
