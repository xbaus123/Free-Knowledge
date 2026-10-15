# Python: Splitting Code Across Files

Real programs are split into **modules**: one file per idea, imported where needed. In Python every `.py` file is a module, and `import` makes one file's functions available in another:

```python
from text_utils import words   # loads text_utils.py and takes its words() function
```

This lesson has several files. Use the **file tree** on the left to look around:

- `text_utils.py` is a helper module someone else wrote. It's **locked** (🔒), so you can read it but not change it.
- `data/sample.txt` is a text file your code will process.
- `solution.py` is where you work.

## Your task

In `solution.py`, finish `word_count(text)` so it returns a dictionary mapping each word to how many times it appears. Use `words()` from `text_utils` to split the text.

- `word_count("the cat and the hat")` → `{"the": 2, "cat": 1, "and": 1, "hat": 1}`

Want to experiment first? Open the **Scratchpad** from the top bar to run any code you like. It isn't graded.
