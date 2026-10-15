# JavaScript: Summing an Array

Arrays can be walked with a `for...of` loop, or reduced to a single value with `reduce`:

```js
const total = [1, 2, 3].reduce((acc, n) => acc + n, 0);
```

## Your task

Export a function `sum(numbers)` that returns the sum of an array of numbers. An empty array sums to `0`.
