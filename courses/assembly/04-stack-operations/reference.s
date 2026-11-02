    .intel_syntax noprefix
    .text

# void reverse(long *xs, long n)
#   xs in rdi, n in rsi
    .globl reverse
reverse:
    xor ecx, ecx
reverse_push:
    cmp rcx, rsi
    jge reverse_pop_start
    push qword ptr [rdi + rcx*8]
    inc rcx
    jmp reverse_push
reverse_pop_start:
    xor ecx, ecx
reverse_pop:
    cmp rcx, rsi
    jge reverse_done
    pop qword ptr [rdi + rcx*8]
    inc rcx
    jmp reverse_pop
reverse_done:
    ret

# long square(long x)
#   x in rdi
    .globl square
square:
    mov rax, rdi
    imul rax, rdi
    ret

# long sum_of_squares(long a, long b)
#   a in rdi, b in rsi
    .globl sum_of_squares
sum_of_squares:
    push rbx            # save the caller's rbx; also aligns the stack for call
    mov rbx, rsi        # keep b safe across the first call
    call square         # rax = a * a
    mov rdi, rbx
    mov rbx, rax        # now keep a * a safe across the second call
    call square         # rax = b * b
    add rax, rbx
    pop rbx
    ret
