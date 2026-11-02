# FreeKnowledge register check for assembly lessons (see EXPECT_PRESERVES
# in fk_asm.h).
#
# fk_check_trampoline stands in for the learner's function: it takes the
# same register arguments, fills the callee-saved registers with sentinels,
# calls fk_check_target, and sets a bit in fk_check_clobbered for each
# register that didn't come back unchanged: rbx 1, rbp 2, r12 4, r13 8,
# r14 16, r15 32, rsp 64. Symbols carry no _ prefix; the C side names them
# with asm labels so this works on macOS, Linux, and Windows.

    .intel_syntax noprefix
    .text

    .globl fk_check_trampoline
fk_check_trampoline:
    push rbx                    # the C caller's registers
    push rbp
    push r12
    push r13
    push r14
    push r15
    sub rsp, 8                  # 16-byte aligned for the call
    mov [rip + fk_check_rsp], rsp

    movabs rbx, 0x5eed0001deadbeef
    movabs rbp, 0x5eed0002deadbeef
    movabs r12, 0x5eed0003deadbeef
    movabs r13, 0x5eed0004deadbeef
    movabs r14, 0x5eed0005deadbeef
    movabs r15, 0x5eed0006deadbeef
    mov rax, [rip + fk_check_target]
    call rax                    # arguments are still in rdi .. r9

    xor ecx, ecx
    movabs rdx, 0x5eed0001deadbeef
    cmp rbx, rdx
    je 1f
    or ecx, 1
1:  movabs rdx, 0x5eed0002deadbeef
    cmp rbp, rdx
    je 2f
    or ecx, 2
2:  movabs rdx, 0x5eed0003deadbeef
    cmp r12, rdx
    je 3f
    or ecx, 4
3:  movabs rdx, 0x5eed0004deadbeef
    cmp r13, rdx
    je 4f
    or ecx, 8
4:  movabs rdx, 0x5eed0005deadbeef
    cmp r14, rdx
    je 5f
    or ecx, 16
5:  movabs rdx, 0x5eed0006deadbeef
    cmp r15, rdx
    je 6f
    or ecx, 32
6:  cmp rsp, [rip + fk_check_rsp]
    je 7f
    or ecx, 64
    mov rsp, [rip + fk_check_rsp]
7:  mov [rip + fk_check_clobbered], rcx

    add rsp, 8
    pop r15
    pop r14
    pop r13
    pop r12
    pop rbp
    pop rbx
    ret                         # the learner's result is still in rax

    .data
    .p2align 3
    .globl fk_check_target
fk_check_target:
    .quad 0
    .globl fk_check_clobbered
fk_check_clobbered:
    .quad 0
fk_check_rsp:
    .quad 0
