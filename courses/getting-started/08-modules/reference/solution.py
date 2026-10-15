from text_utils import words


def word_count(text):
    counts = {}
    for word in words(text):
        counts[word] = counts.get(word, 0) + 1
    return counts
