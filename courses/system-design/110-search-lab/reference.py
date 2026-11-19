"""A full-text search engine: a positional inverted index, BM25 ranking,
phrase queries, and fuzzy matching."""

import heapq
import math
import re

STOPWORDS = frozenset("a an and are as at be by for from in is it of on or the to with".split())


def analyze(text):
    """Text -> [(position, term)]: lowercase runs of letters and digits.

    Stopwords are dropped, but still count as positions, so "state of the
    art" is state at 0 and art at 3.
    """
    words = re.findall(r"[a-z0-9]+", text.lower())
    return [(pos, w) for pos, w in enumerate(words) if w not in STOPWORDS]


class Index:
    def __init__(self, k1=1.2, b=0.75):
        self.k1 = k1
        self.b = b
        self.postings = {}  # term -> {doc_id: [positions]}
        self.doc_len = {}  # doc_id -> number of terms
        self.doc_terms = {}  # doc_id -> set of its terms, to undo add()
        self.total_len = 0  # sum of doc_len, for the average

    # --- 1. Indexing ---------------------------------------------------------

    def add(self, doc_id, text):
        """Index text under doc_id, replacing any earlier version."""
        self.delete(doc_id)
        terms = analyze(text)
        self.doc_len[doc_id] = len(terms)
        self.total_len += len(terms)
        self.doc_terms[doc_id] = {t for _, t in terms}
        for pos, term in terms:
            self.postings.setdefault(term, {}).setdefault(doc_id, []).append(pos)

    def delete(self, doc_id):
        for term in self.doc_terms.pop(doc_id, ()):
            docs = self.postings[term]
            del docs[doc_id]
            if not docs:
                del self.postings[term]
        self.total_len -= self.doc_len.pop(doc_id, 0)

    # --- 2. Ranking ----------------------------------------------------------

    def idf(self, term):
        n = len(self.postings.get(term, ()))
        return math.log(1 + (len(self.doc_len) - n + 0.5) / (n + 0.5))

    def search(self, query, k=10, fuzziness=0):
        """The top k (doc_id, score) pairs for query, best first."""
        terms = {t for _, t in analyze(query)}
        if fuzziness:
            terms = {m for t in terms for m in self.fuzzy_terms(t, fuzziness)}
        if not self.doc_len:
            return []
        avgdl = self.total_len / len(self.doc_len)
        scores = {}
        for term in terms:
            docs = self.postings.get(term)
            if not docs:
                continue
            idf = self.idf(term)
            for doc_id, positions in docs.items():
                tf = len(positions)
                norm = self.k1 * (1 - self.b + self.b * self.doc_len[doc_id] / avgdl)
                scores[doc_id] = scores.get(doc_id, 0.0) + idf * tf * (self.k1 + 1) / (tf + norm)
        return heapq.nsmallest(k, scores.items(), key=lambda kv: (-kv[1], kv[0]))

    # --- 3. Phrases ----------------------------------------------------------

    def phrase(self, query):
        """The sorted ids of documents containing query's terms in order, at
        the same relative positions."""
        terms = analyze(query)
        if not terms:
            return []
        start = terms[0][0]
        offsets = [(pos - start, term) for pos, term in terms]
        lists = [self.postings.get(term) for _, term in offsets]
        if not all(lists):
            return []
        # Intersect starting from the rarest term: the fewest candidates.
        candidates = set(min(lists, key=len))
        for docs in lists:
            candidates &= docs.keys()
        found = []
        for doc_id in candidates:
            sets = [(off, set(self.postings[term][doc_id])) for off, term in offsets]
            if any(all(p + off in s for off, s in sets) for p in self.postings[offsets[0][1]][doc_id]):
                found.append(doc_id)
        return sorted(found)

    # --- 4. Fuzzy matching ---------------------------------------------------

    def fuzzy_terms(self, term, max_edits):
        """Every indexed term within max_edits of term."""
        return {
            t
            for t in self.postings
            if abs(len(t) - len(term)) <= max_edits and levenshtein(t, term) <= max_edits
        }

    def suggest(self, word, max_edits=2, limit=5):
        """'Did you mean': indexed terms close to word, closest first, then
        the most common, then alphabetically."""
        word = word.lower()
        ranked = sorted(
            self.fuzzy_terms(word, max_edits),
            key=lambda t: (levenshtein(t, word), -len(self.postings[t]), t),
        )
        return ranked[:limit]


# --- Edit distance ----------------------------------------------------------


def levenshtein(a, b):
    """The fewest single-character insertions, deletions, and substitutions
    that turn a into b."""
    if len(a) < len(b):
        a, b = b, a
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
