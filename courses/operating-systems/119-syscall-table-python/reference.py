"""A system-call interface: a table of numbered calls and three ways to pass parameters."""

NUM_PARAM_REGISTERS = 5


class SyscallInterface:
    def __init__(self):
        self.table = {}

    def register(self, number, name, handler, nparams):
        if number in self.table:
            raise ValueError(f"system call {number} is already registered")
        if any(n == name for n, _, _ in self.table.values()):
            raise ValueError(f"{name} is already registered")
        self.table[number] = (name, handler, nparams)

    def number_of(self, name):
        for number, (n, _, _) in self.table.items():
            if n == name:
                return number
        raise KeyError(name)

    def get_params(self, method, nparams, regs, memory, stack):
        if method == "registers":
            if nparams > NUM_PARAM_REGISTERS:
                raise ValueError("more parameters than registers")
            return list(regs[1:1 + nparams])
        if method == "block":
            x = regs[1]
            return list(memory[x:x + nparams])
        if method == "stack":
            return [stack.pop() for _ in range(nparams)]
        raise ValueError(f"unknown method {method!r}")

    def syscall(self, regs, method="registers", memory=None, stack=None):
        entry = self.table.get(regs[0])
        if entry is None:
            return -1
        _, handler, nparams = entry
        return handler(*self.get_params(method, nparams, regs, memory, stack))


def api_call(iface, name, *args):
    number = iface.number_of(name)
    if len(args) <= NUM_PARAM_REGISTERS:
        return iface.syscall([number, *args])
    return iface.syscall([number, 0], method="block", memory=list(args))
