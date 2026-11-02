    .intel_syntax noprefix
    .text

# long max2(long a, long b)
#   a in rdi, b in rsi
    .globl max2
max2:
    # Return the larger of a and b
    mov eax, 0
    ret

# long sum_array(const long *xs, long n)
#   xs in rdi, n in rsi
    .globl sum_array
sum_array:
    # Return xs[0] + xs[1] + ... + xs[n - 1]
    mov eax, 0
    ret
