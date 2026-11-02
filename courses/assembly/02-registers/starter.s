    .intel_syntax noprefix
    .text

# long linear(long a, long x, long b)
#   a in rdi, x in rsi, b in rdx
    .globl linear
linear:
    # Return a * x + b
    mov eax, 0
    ret

# long low_byte(long x)
#   x in rdi
    .globl low_byte
low_byte:
    # Return the lowest 8 bits of x
    mov eax, 0
    ret
