# C: Largest Element

In C, a function that takes an array receives a **pointer** to its first element, so the length has to be passed separately:

```c
int first(const int *xs, int n) { return xs[0]; }
```

## Your task

Implement `int max_of(const int *xs, int n)` that returns the largest of the `n` values in `xs`. You can assume `n >= 1`.

Don't write a `main` function; the tests provide one.
