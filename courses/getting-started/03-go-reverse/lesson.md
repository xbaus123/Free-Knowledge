# Go: Reversing a String

Go strings are bytes, but text is made of **runes** (Unicode code points). Converting with `[]rune(s)` lets you work with characters instead of bytes, so `"héllo"` reverses correctly.

## Your task

Write `Reverse(s string) string` that returns `s` reversed, character by character.

- `Reverse("hello")` → `"olleh"`
- `Reverse("héllo")` → `"olléh"`
