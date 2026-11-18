"""A toy machine with a mode bit, privileged instructions, system calls, and a timer."""

KERNEL = 0
USER = 1

PRIVILEGED = {"set_timer", "disable_interrupts", "io", "set_mode", "clear_memory", "halt"}


def is_privileged(instruction):
    """True if the part of instruction before any ":" is in PRIVILEGED.
    "io:disk0" -> True, "add" -> False, "syscall:read" -> False."""
    # TODO
    pass


class Machine:
    def __init__(self):
        self.mode = KERNEL   # the OS is in control before any user program runs
        self.timer = 0       # 0 means the timer isn't set
        self.log = []

    def handle_syscall(self, name):
        """The kernel's system-call handler. Runs in kernel mode. (Done for you.)"""
        self.log.append(f"syscall:{name}")

    def set_timer(self, ticks):
        """Privileged: raise PermissionError in user mode, else set self.timer."""
        # TODO
        pass

    def run(self, program):
        """Run a user program (a list of instruction strings) in user mode.

        Raise PermissionError unless called in kernel mode. Then switch to
        USER and go through the instructions:

          privileged      -> kernel mode, log "trap:illegal:<instr>", return ("killed", n)
          "div0"          -> kernel mode, log "trap:divide-by-zero",  return ("killed", n)
          "syscall:<name>"-> kernel mode, self.handle_syscall(name), back to user mode
          anything else   -> ordinary instruction, nothing to do

        n counts completed instructions (not the one that traps). After each
        completed instruction, if self.timer > 0, decrement it; if it hits 0,
        go to kernel mode, log "interrupt:timer", and return ("timer", n).

        At the end of the program: kernel mode, log "exit", return ("done", n).
        """
        # TODO
        pass


if __name__ == "__main__":
    m = Machine()
    m.set_timer(3)
    print(m.run(["load", "syscall:write", "add", "add", "store"]))   # ('timer', 3)
    print(m.log, m.mode)                       # ['syscall:write', 'interrupt:timer'] 0

    m = Machine()
    print(m.run(["load", "io:disk0", "store"]))   # ('killed', 1)
    print(m.log)                                  # ['trap:illegal:io:disk0']
