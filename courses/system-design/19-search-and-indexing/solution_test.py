import random
import time
import unittest

from solution import Index, levenshtein

DOCS = {
    "d1": "The quick brown fox jumps over the lazy dog",
    "d2": "A quick brown dog outpaces a quick red fox",
    "d3": "Lazy dogs sleep all day",
    "d4": "Foxes are quick and clever; the fox is a canid",
    "d5": "State of the art search engines use inverted indexes",
}


def corpus():
    ix = Index()
    for doc_id, text in DOCS.items():
        ix.add(doc_id, text)
    return ix


def ids(results):
    return [doc_id for doc_id, _ in results]


class IndexingTest(unittest.TestCase):
    def test_postings(self):
        """records every position of every term, skipping stopwords"""
        ix = corpus()
        self.assertEqual(ix.postings["quick"], {"d1": [1], "d2": [1, 6], "d4": [2]})
        self.assertEqual(ix.postings["art"], {"d5": [3]}, "stopwords still take up positions")
        self.assertNotIn("the", ix.postings)
        self.assertEqual(ix.doc_len, {"d1": 7, "d2": 7, "d3": 5, "d4": 5, "d5": 7})

    def test_delete(self):
        """deletes a document from every postings list"""
        ix = corpus()
        ix.delete("d3")
        self.assertNotIn("d3", ix.doc_len)
        self.assertNotIn("sleep", ix.postings, "terms with no documents left are gone")
        self.assertEqual(ix.postings["lazy"], {"d1": [7]})
        ix.delete("missing")  # no error

    def test_replace(self):
        """replaces a document added again under the same id"""
        ix = corpus()
        ix.add("d1", "an entirely different story")
        self.assertNotIn("d1", ix.postings["quick"])
        self.assertNotIn("jumps", ix.postings)
        self.assertEqual(ix.postings["story"], {"d1": [3]})
        self.assertEqual(ix.doc_len["d1"], 3)


class RankingTest(unittest.TestCase):
    def test_bm25(self):
        """scores with BM25"""
        results = corpus().search("quick fox")
        self.assertEqual(ids(results), ["d2", "d4", "d1"])
        for (_, got), want in zip(results, [1.227138169774507, 1.1706866671964735, 1.023943213091066]):
            self.assertAlmostEqual(got, want, places=6)
        self.assertAlmostEqual(corpus().search("lazy")[0][1], 0.9507478962983436, places=6)

    def test_short_documents_win(self):
        """favors the shorter of two documents with the same matches"""
        self.assertEqual(ids(corpus().search("lazy")), ["d3", "d1"])

    def test_rare_terms_weigh_more(self):
        """weighs rare terms above common ones"""
        ix = Index()
        for i in range(20):
            ix.add(f"common{i:02}", "database " * 3 + f"filler{i}")
        ix.add("rare", "database raft")
        ix.add("both", "consensus raft")
        top = ix.search("database raft", k=3)
        self.assertEqual(ids(top)[0], "rare")
        self.assertGreater(dict(ix.search("raft"))["both"], dict(ix.search("database", k=30))["common00"])

    def test_saturation(self):
        """saturates term frequency instead of counting it linearly"""
        ix = Index()
        ix.add("once", "raft " + "x " * 9)
        ix.add("tenfold", "raft " * 10)
        ix.add("other", "paxos " * 10)
        scores = dict(ix.search("raft"))
        self.assertGreater(scores["tenfold"], scores["once"])
        self.assertLess(scores["tenfold"], 2.2 * scores["once"], "10 occurrences shouldn't score anywhere near 10 times one")

    def test_top_k_and_ties(self):
        """returns the top k, breaking ties by document id"""
        self.assertEqual(ids(corpus().search("fox", k=2)), ["d4", "d1"])
        self.assertEqual(corpus().search("nothing matches"), [])
        self.assertEqual(Index().search("fox"), [])

    def test_deleted_documents_vanish(self):
        """doesn't return deleted documents"""
        ix = corpus()
        ix.delete("d3")
        self.assertEqual(ids(ix.search("lazy")), ["d1"])

    def test_duplicate_query_terms(self):
        """counts each distinct query term once"""
        self.assertEqual(corpus().search("fox fox FOX"), corpus().search("fox"))

    def test_uses_postings(self):
        """reads only the postings of the query's terms"""
        rng = random.Random(7)
        vocab = [f"w{i}" for i in range(3000)]
        ix = Index()
        for d in range(20000):
            ix.add(d, " ".join(rng.choice(vocab[:200]) for _ in range(20)) + f" rare{d % 5000}")
        start = time.perf_counter()
        for q in range(1000):
            ix.search(f"rare{q} rare{q + 1}", k=5)
        elapsed = time.perf_counter() - start
        self.assertLess(elapsed, 0.5, f"1,000 searches took {elapsed:.2f}s: don't loop over every document")


class PhraseTest(unittest.TestCase):
    def test_adjacent(self):
        """finds terms next to each other, in order"""
        ix = corpus()
        self.assertEqual(ix.phrase("quick brown"), ["d1", "d2"])
        self.assertEqual(ix.phrase("brown fox"), ["d1"])
        self.assertEqual(ix.phrase("fox brown"), [])
        self.assertEqual(ix.phrase("fox jumps over the lazy dog"), ["d1"])

    def test_stopword_gaps(self):
        """keeps the gaps stopwords leave"""
        ix = corpus()
        ix.add("d6", "Art of the state")
        ix.add("d7", "state art")
        self.assertEqual(ix.phrase("state of the art"), ["d5"])
        self.assertEqual(ix.phrase("state art"), ["d7"])

    def test_repeated_terms(self):
        """checks every occurrence of the first term"""
        ix = Index()
        ix.add("x", "red fox red dog red fox")
        ix.add("y", "red red dog")
        self.assertEqual(ix.phrase("red dog"), ["x", "y"])
        self.assertEqual(ix.phrase("red red"), ["y"])

    def test_missing(self):
        """returns nothing for unknown terms or an empty query"""
        ix = corpus()
        self.assertEqual(ix.phrase("quick unicorn"), [])
        self.assertEqual(ix.phrase("the of"), [])


class FuzzyTest(unittest.TestCase):
    def test_levenshtein(self):
        """counts insertions, deletions, and substitutions"""
        self.assertEqual(levenshtein("kitten", "sitting"), 3)
        self.assertEqual(levenshtein("", "abc"), 3)
        self.assertEqual(levenshtein("flaw", "lawn"), 2)
        self.assertEqual(levenshtein("same", "same"), 0)
        self.assertEqual(levenshtein("quick", "quikc"), 2, "a transposition is two edits here")

    def test_fuzzy_terms(self):
        """finds indexed terms within the edit distance"""
        ix = corpus()
        self.assertEqual(ix.fuzzy_terms("dgo", 2), {"day", "dog", "dogs"})
        self.assertEqual(ix.fuzzy_terms("dog", 0), {"dog"})
        self.assertEqual(ix.fuzzy_terms("foxs", 1), {"fox", "foxes"})

    def test_suggest(self):
        """suggests the closest, then the most common terms"""
        ix = corpus()
        self.assertEqual(ix.suggest("quikc"), ["quick"])
        self.assertEqual(ix.suggest("Dgo"), ["dog", "day", "dogs"], "all two edits away: dog is in two documents")
        ix.add("d8", "cog cog")
        ix.add("d9", "cog")
        self.assertEqual(ix.suggest("dog", max_edits=1), ["dog", "cog", "dogs"])
        self.assertEqual(ix.suggest("dog", max_edits=1, limit=2), ["dog", "cog"])

    def test_fuzzy_search(self):
        """searches with typos when fuzziness is set"""
        ix = corpus()
        self.assertEqual(ix.search("quikc fxo"), [])
        self.assertEqual(ids(ix.search("quikc fxo", fuzziness=2)), ["d2", "d4", "d1"])
        self.assertEqual(ids(ix.search("lazzy", fuzziness=1)), ["d3", "d1"])


if __name__ == "__main__":
    unittest.main()
