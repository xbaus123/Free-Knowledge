"""A toy machine with a mode bit, privileged instructions, system calls, and a timer."""

KERNEL = 0
USER = 1

PRIVILEGED = {"set_timer", "disable_interrupts", "io", "set_mode", "clear_memory", "halt"}


def is_privileged(instruction):
    return instruction.split(":", 1)[0] in PRIVILEGED


class Machine:
    def __init__(self):
        self.mode = KERNEL
        self.timer = 0
        self.log = []

    def handle_syscall(self, name):
        """The kernel's system-call handler. Runs in kernel mode."""
        self.log.append(f"syscall:{name}")

    def set_timer(self, ticks):
        if self.mode != KERNEL:
            raise PermissionError("set_timer is privileged")
        self.timer = ticks

    def _trap(self, entry):
        self.mode = KERNEL
        self.log.append(entry)

    def run(self, program):
        if self.mode != KERNEL:
            raise PermissionError("only the kernel can start a program")
        self.mode = USER
        done = 0
        for instruction in program:
            if is_privileged(instruction):
                self._trap(f"trap:illegal:{instruction}")
                return ("killed", done)
            if instruction == "div0":
                self._trap("trap:divide-by-zero")
                return ("killed", done)
            if instruction.startswith("syscall:"):
                self.mode = KERNEL
                self.handle_syscall(instruction.split(":", 1)[1])
                self.mode = USER
            done += 1
            if self.timer > 0:
                self.timer -= 1
                if self.timer == 0:
                    self._trap("interrupt:timer")
                    return ("timer", done)
        self._trap("exit")
        return ("done", done)
