    .intel_syntax noprefix
    .text

# long max2(long a, long b)
#   a in rdi, b in rsi
    .globl max2
max2:
    mov rax, rdi
    cmp rax, rsi
    jge max2_done
    mov rax, rsi
max2_done:
    ret

# long sum_array(const long *xs, long n)
#   xs in rdi, n in rsi
    .globl sum_array
sum_array:
    xor eax, eax
    xor ecx, ecx
sum_array_loop:
    cmp rcx, rsi
    jge sum_array_done
    add rax, [rdi + rcx*8]
    inc rcx
    jmp sum_array_loop
sum_array_done:
    ret
