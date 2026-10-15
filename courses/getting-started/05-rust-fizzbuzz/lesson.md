# Rust: FizzBuzz

Rust's `match` can check several conditions at once by matching on a tuple:

```rust
match (n % 2, n % 5) {
    (0, 0) => "both",
    (0, _) => "even",
    _ => "other",
}
```

## Your task

Write `fn fizzbuzz(n: u32) -> String` that returns:

- `"FizzBuzz"` if `n` is divisible by 3 and 5
- `"Fizz"` if divisible by 3
- `"Buzz"` if divisible by 5
- otherwise the number itself, as a string
