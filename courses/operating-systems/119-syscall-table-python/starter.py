"""A system-call interface: a table of numbered calls and three ways to pass parameters."""

NUM_PARAM_REGISTERS = 5   # registers r1..r5 can carry parameters; r0 holds the call number


class SyscallInterface:
    def __init__(self):
        # number -> (name, handler, nparams)
        self.table = {}

    def register(self, number, name, handler, nparams):
        """Add a system call to the table. Raise ValueError if the number
        (or the name) is already taken."""
        # TODO
        pass

    def number_of(self, name):
        """The number for a system call name. Raise KeyError if unknown."""
        # TODO
        pass

    def get_params(self, method, nparams, regs, memory, stack):
        """Collect nparams parameters, first parameter first.

        "registers": they're in regs[1], regs[2], ... Raise ValueError if
                     nparams > NUM_PARAM_REGISTERS.
        "block":     regs[1] holds an address X; they're memory[X], memory[X+1], ...
        "stack":     the program pushed them last-first, so popping gives
                     the first parameter first. Pop them (the stack shrinks).
        Any other method: raise ValueError.
        """
        # TODO
        pass

    def syscall(self, regs, method="registers", memory=None, stack=None):
        """Trap into the kernel. regs[0] is the system-call number.

        Unknown number: return -1. Otherwise gather the parameters with
        get_params and return handler(*params).
        """
        # TODO
        pass


def api_call(iface, name, *args):
    """A library wrapper, like the C library's: look up the call's number by
    name, load the number and the arguments into registers, and trap.
    Use the "block" method instead when there are too many arguments for
    registers: put them in a fresh memory list and pass address 0."""
    # TODO
    pass


if __name__ == "__main__":
    out = []
    iface = SyscallInterface()
    iface.register(4, "write", lambda fd, text: out.append(text) or len(text), 2)
    print(iface.syscall([4, 1, "hi"]))                                   # 2
    print(iface.syscall([4, 7], method="block", memory=[0] * 7 + [1, "yo"]))  # 2
    print(iface.syscall([4], method="stack", stack=["abc", 1]))          # 3
    print(api_call(iface, "write", 1, "Greetings"))                       # 9
    print(out)                                       # ['hi', 'yo', 'abc', 'Greetings']
