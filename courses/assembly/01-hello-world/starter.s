    .intel_syntax noprefix
    .text

# long answer(void)
    .globl answer
answer:
    # Return 42
    mov eax, 0
    ret

# const char *greeting(void)
    .globl greeting
greeting:
    # Return the address of "Hello, World!" (define it in a .data section)
    mov eax, 0
    ret
