    .intel_syntax noprefix
    .text

# void reverse(long *xs, long n)
#   xs in rdi, n in rsi
    .globl reverse
reverse:
    # Push xs[0] .. xs[n - 1], then pop them back into xs[0] .. xs[n - 1]
    ret

# long square(long x)
#   x in rdi
    .globl square
square:
    # Return x * x
    mov eax, 0
    ret

# long sum_of_squares(long a, long b)
#   a in rdi, b in rsi
    .globl sum_of_squares
sum_of_squares:
    # Return square(a) + square(b), calling square twice
    mov eax, 0
    ret
