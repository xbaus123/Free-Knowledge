# Phrases, Positions, and Fuzzy Matching

*Chapter 4 · Search, Blobs, Time Series, and Encoding.*

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

Next, a short check on what you just read.
