    .intel_syntax noprefix
    .text

# long answer(void)
    .globl answer
answer:
    mov eax, 42
    ret

# const char *greeting(void)
    .globl greeting
greeting:
    lea rax, [rip + message]
    ret

    .data
message:
    .asciz "Hello, World!"
