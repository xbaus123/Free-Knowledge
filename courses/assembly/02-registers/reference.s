    .intel_syntax noprefix
    .text

# long linear(long a, long x, long b)
#   a in rdi, x in rsi, b in rdx
    .globl linear
linear:
    mov rax, rdi
    imul rax, rsi
    add rax, rdx
    ret

# long low_byte(long x)
#   x in rdi
    .globl low_byte
low_byte:
    movzx eax, dil
    ret
