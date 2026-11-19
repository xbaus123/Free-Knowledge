"""Structure experiments: checking layering rules and counting microkernel overhead."""


def layer_violations(levels, calls):
    return [(a, b) for a, b in calls if levels[b] >= levels[a]]


def assign_layers(uses):
    names = set(uses)
    for deps in uses.values():
        names.update(deps)
    layer = {}
    visiting = set()

    def visit(name):
        if name in layer:
            return layer[name]
        if name in visiting:
            raise ValueError(f"cycle through {name}")
        visiting.add(name)
        deps = uses.get(name, [])
        layer[name] = 1 + max(visit(d) for d in deps) if deps else 0
        visiting.discard(name)
        return layer[name]

    for name in sorted(names):
        visit(name)
    return layer


def mode_switches(path, modes):
    cost = {("kernel", "kernel"): 0, ("user", "kernel"): 1, ("kernel", "user"): 1, ("user", "user"): 2}
    return sum(cost[(modes[a], modes[b])] for a, b in zip(path, path[1:]))
