"""Helpers for working with text. (Read-only in this lesson.)"""

import re


def words(text):
    """Split text into lowercase words, ignoring punctuation.

    >>> words("Hello, hello world!")
    ['hello', 'hello', 'world']
    """
    return re.findall(r"[a-z']+", text.lower())
