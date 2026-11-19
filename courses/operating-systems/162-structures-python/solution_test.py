import unittest

from solution import assign_layers, layer_violations, mode_switches


class Violations(unittest.TestCase):
    LEVELS = {"hw": 0, "drivers": 1, "mem": 2, "fs": 3, "ui": 4}

    def test_clean(self):
        """Calls that only go down are fine"""
        calls = [("ui", "fs"), ("fs", "mem"), ("fs", "drivers"), ("ui", "hw")]
        self.assertEqual(layer_violations(self.LEVELS, calls), [])

    def test_upward_call(self):
        """Calling a higher layer breaks the rule"""
        calls = [("ui", "fs"), ("drivers", "mem"), ("fs", "mem"), ("hw", "ui")]
        self.assertEqual(layer_violations(self.LEVELS, calls), [("drivers", "mem"), ("hw", "ui")])

    def test_same_layer(self):
        """Calling a module in the same layer breaks it too"""
        levels = {"a": 1, "b": 1, "hw": 0}
        self.assertEqual(layer_violations(levels, [("a", "b"), ("a", "hw")]), [("a", "b")])

    def test_no_calls(self):
        """No calls, no violations"""
        self.assertEqual(layer_violations(self.LEVELS, []), [])


class Assign(unittest.TestCase):
    def test_example(self):
        """The example from the lesson"""
        got = assign_layers({"fs": ["mem", "driver"], "driver": ["hw"], "mem": ["hw"]})
        self.assertEqual(got, {"fs": 2, "mem": 1, "driver": 1, "hw": 0})

    def test_longest_path_wins(self):
        """A module sits above the HIGHEST thing it uses"""
        uses = {"ui": ["fs", "hw"], "fs": ["cache"], "cache": ["disk"], "disk": ["hw"]}
        got = assign_layers(uses)
        self.assertEqual(got["hw"], 0)
        self.assertEqual(got["disk"], 1)
        self.assertEqual(got["cache"], 2)
        self.assertEqual(got["fs"], 3)
        self.assertEqual(got["ui"], 4)

    def test_keys_with_no_uses(self):
        """A key with an empty list is layer 0"""
        self.assertEqual(assign_layers({"hw": [], "a": ["hw"]}), {"hw": 0, "a": 1})

    def test_result_is_valid(self):
        """The layering it finds has no violations"""
        uses = {"a": ["b", "c"], "b": ["d"], "c": ["d", "e"], "e": ["d"]}
        levels = assign_layers(uses)
        calls = [(m, d) for m, ds in uses.items() for d in ds]
        self.assertEqual(layer_violations(levels, calls), [])
        self.assertEqual(set(levels), {"a", "b", "c", "d", "e"})

    def test_cycle(self):
        """Memory needs the disk driver and the disk driver needs memory: no layering"""
        with self.assertRaises(ValueError):
            assign_layers({"mem": ["disk"], "disk": ["mem"]})

    def test_longer_cycle(self):
        """Cycles can be long"""
        with self.assertRaises(ValueError):
            assign_layers({"a": ["b"], "b": ["c"], "c": ["a"], "d": []})

    def test_self_cycle(self):
        """A module can't use itself"""
        with self.assertRaises(ValueError):
            assign_layers({"a": ["a"]})

    def test_empty(self):
        """No modules"""
        self.assertEqual(assign_layers({}), {})


class Switches(unittest.TestCase):
    PATH = ["app", "fs", "driver", "fs", "app"]

    def test_monolithic(self):
        """Into the kernel once and back out once"""
        modes = {"app": "user", "fs": "kernel", "driver": "kernel"}
        self.assertEqual(mode_switches(self.PATH, modes), 2)

    def test_microkernel(self):
        """Every hop between user-space servers is a message: 2 switches"""
        modes = {"app": "user", "fs": "user", "driver": "user"}
        self.assertEqual(mode_switches(self.PATH, modes), 8)

    def test_kernel_hop(self):
        """Kernel-to-kernel is free"""
        self.assertEqual(mode_switches(["a", "b"], {"a": "kernel", "b": "kernel"}), 0)

    def test_one_crossing(self):
        """User to kernel, or kernel to user, is one switch"""
        modes = {"u": "user", "k": "kernel"}
        self.assertEqual(mode_switches(["u", "k"], modes), 1)
        self.assertEqual(mode_switches(["k", "u"], modes), 1)

    def test_short_paths(self):
        """A path with fewer than two stops has no hops"""
        self.assertEqual(mode_switches([], {}), 0)
        self.assertEqual(mode_switches(["app"], {"app": "user"}), 0)

    def test_microkernel_costs_more(self):
        """The same request always costs at least as much on a microkernel"""
        path = ["app", "net", "driver", "net", "fs", "driver", "fs", "net", "app"]
        mono = {"app": "user", "net": "kernel", "fs": "kernel", "driver": "kernel"}
        micro = {"app": "user", "net": "user", "fs": "user", "driver": "user"}
        self.assertEqual(mode_switches(path, mono), 2)
        self.assertEqual(mode_switches(path, micro), 16)


if __name__ == "__main__":
    unittest.main()
