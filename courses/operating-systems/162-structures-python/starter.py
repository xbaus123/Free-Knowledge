"""Structure experiments: checking layering rules and counting microkernel overhead."""


def layer_violations(levels, calls):
    """levels: {module: layer number} (0 is the hardware).
    calls: a list of (caller, callee) pairs.

    In a layered system a module may only use modules in LOWER layers.
    Return the list of calls that break the rule, in their original order.
    """
    # TODO
    pass


def assign_layers(uses):
    """uses: {module: [modules it uses]}. A module that appears only in
    someone's list, never as a key, uses nothing.

    Give every module the lowest layer it can have: 0 if it uses nothing,
    otherwise 1 + the highest layer among the modules it uses.
    Return {module: layer} for every module mentioned anywhere.
    If the modules use each other in a cycle, no layering exists:
    raise ValueError.
    """
    # TODO
    pass


def mode_switches(path, modes):
    """path: the components a request visits, in order, e.g.
    ["app", "fs", "driver", "fs", "app"].
    modes: {component: "user" or "kernel"}.

    Count the mode switches for each hop from one component to the next:
      kernel -> kernel : 0  (a plain function call inside the kernel)
      user <-> kernel  : 1  (a system call, or a return to user mode)
      user  -> user    : 2  (a message: into the kernel, then out to the receiver)
    Return the total.
    """
    # TODO
    pass


if __name__ == "__main__":
    print(layer_violations({"hw": 0, "mem": 1, "fs": 2}, [("fs", "mem"), ("mem", "fs")]))
    # [('mem', 'fs')]
    print(assign_layers({"fs": ["mem", "driver"], "driver": ["hw"], "mem": ["hw"]}))
    # {'fs': 2, 'mem': 1, 'driver': 1, 'hw': 0}  (any order)
    request = ["app", "fs", "driver", "fs", "app"]
    print(mode_switches(request, {"app": "user", "fs": "kernel", "driver": "kernel"}))  # 2
    print(mode_switches(request, {"app": "user", "fs": "user", "driver": "user"}))      # 8
