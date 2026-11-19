# Compressing Postings and Analyzing Text

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

## Making postings small and fast

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

Next, a short check on what you just read.
