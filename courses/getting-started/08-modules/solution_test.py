import unittest

from solution import word_count


class WordCountTest(unittest.TestCase):
    def test_simple_sentence(self):
        """counts repeated words"""
        self.assertEqual(word_count("the cat and the hat"), {"the": 2, "cat": 1, "and": 1, "hat": 1})

    def test_ignores_case_and_punctuation(self):
        """treats 'The' and 'the.' as the same word"""
        self.assertEqual(word_count("The end. the END!"), {"the": 2, "end": 2})

    def test_sample_file(self):
        """counts the words in data/sample.txt"""
        with open("data/sample.txt") as f:
            counts = word_count(f.read())
        self.assertEqual(counts["the"], 4)
        self.assertEqual(counts["fox"], 2)

    def test_empty_text(self):
        """returns an empty dictionary for empty text"""
        self.assertEqual(word_count(""), {})
