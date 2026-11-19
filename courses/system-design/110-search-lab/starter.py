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

    # --- 1. Indexing ---------------------------------------------------------

    def add(self, doc_id, text):
        """Index text under doc_id, replacing any earlier version."""
        raise NotImplementedError

    def delete(self, doc_id):
        raise NotImplementedError

    # --- 2. Ranking ----------------------------------------------------------

    def idf(self, term):
        n = len(self.postings.get(term, ()))
        return math.log(1 + (len(self.doc_len) - n + 0.5) / (n + 0.5))

    def search(self, query, k=10, fuzziness=0):
        """The top k (doc_id, score) pairs for query, best first."""
        raise NotImplementedError

    # --- 3. Phrases ----------------------------------------------------------

    def phrase(self, query):
        """The sorted ids of documents containing query's terms in order, at
        the same relative positions."""
        raise NotImplementedError

    # --- 4. Fuzzy matching ---------------------------------------------------

    def fuzzy_terms(self, term, max_edits):
        """Every indexed term within max_edits of term."""
        raise NotImplementedError

    def suggest(self, word, max_edits=2, limit=5):
        """'Did you mean': indexed terms close to word, closest first, then
        the most common, then alphabetically."""
        raise NotImplementedError


# --- Edit distance ----------------------------------------------------------


def levenshtein(a, b):
    """The fewest single-character insertions, deletions, and substitutions
    that turn a into b."""
    raise NotImplementedError
