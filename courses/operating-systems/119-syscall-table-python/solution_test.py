import unittest

from solution import NUM_PARAM_REGISTERS, SyscallInterface, api_call


def make():
    out = []
    iface = SyscallInterface()
    iface.register(4, "write", lambda fd, text: out.append((fd, text)) or len(text), 2)
    iface.register(20, "getpid", lambda: 1234, 0)
    iface.register(13, "sum7", lambda *xs: sum(xs), 7)
    return iface, out


class Table(unittest.TestCase):
    def test_register_and_lookup(self):
        """Calls are found by number and by name"""
        iface, _ = make()
        self.assertEqual(iface.table[4][0], "write")
        self.assertEqual(iface.number_of("write"), 4)
        self.assertEqual(iface.number_of("getpid"), 20)

    def test_duplicate_number(self):
        """Two calls can't share a number"""
        iface, _ = make()
        with self.assertRaises(ValueError):
            iface.register(4, "other", lambda: 0, 0)

    def test_duplicate_name(self):
        """Two numbers can't share a name"""
        iface, _ = make()
        with self.assertRaises(ValueError):
            iface.register(99, "write", lambda: 0, 0)

    def test_unknown_name(self):
        """Looking up a missing name raises KeyError"""
        iface, _ = make()
        with self.assertRaises(KeyError):
            iface.number_of("fork")

    def test_unknown_number(self):
        """An unknown system-call number returns -1"""
        iface, _ = make()
        self.assertEqual(iface.syscall([999, 1, 2]), -1)


class Registers(unittest.TestCase):
    def test_registers(self):
        """Parameters in r1, r2, ..."""
        iface, out = make()
        self.assertEqual(iface.syscall([4, 1, "hello"]), 5)
        self.assertEqual(out, [(1, "hello")])

    def test_no_params(self):
        """A call with no parameters"""
        iface, _ = make()
        self.assertEqual(iface.syscall([20]), 1234)

    def test_extra_registers_ignored(self):
        """Only nparams registers are read"""
        iface, out = make()
        iface.syscall([4, 2, "x", "junk", "junk"])
        self.assertEqual(out, [(2, "x")])

    def test_too_many_for_registers(self):
        """More parameters than registers can't use the register method"""
        iface, _ = make()
        with self.assertRaises(ValueError):
            iface.syscall([13, 1, 2, 3, 4, 5, 6, 7])

    def test_unknown_method(self):
        """Only three methods exist"""
        iface, _ = make()
        with self.assertRaises(ValueError):
            iface.syscall([20], method="carrier-pigeon")


class Block(unittest.TestCase):
    def test_block(self):
        """r1 holds the address of the parameter block"""
        iface, out = make()
        memory = ["?"] * 10 + [3, "from block"] + ["?"] * 5
        self.assertEqual(iface.syscall([4, 10], method="block", memory=memory), 10)
        self.assertEqual(out, [(3, "from block")])

    def test_block_has_no_limit(self):
        """Seven parameters fit in a block"""
        iface, _ = make()
        memory = [0, 0] + [1, 2, 3, 4, 5, 6, 7]
        self.assertEqual(iface.syscall([13, 2], method="block", memory=memory), 28)


class Stack(unittest.TestCase):
    def test_stack(self):
        """Parameters pushed last-first come off first-first"""
        iface, out = make()
        stack = ["below"]
        stack.append("text on stack")   # second parameter pushed first
        stack.append(5)                 # first parameter pushed last
        self.assertEqual(iface.syscall([4], method="stack", stack=stack), 13)
        self.assertEqual(out, [(5, "text on stack")])
        self.assertEqual(stack, ["below"])

    def test_stack_has_no_limit(self):
        """Seven parameters fit on the stack"""
        iface, _ = make()
        stack = [7, 6, 5, 4, 3, 2, 1]
        self.assertEqual(iface.syscall([13], method="stack", stack=stack), 28)
        self.assertEqual(stack, [])

    def test_stack_order_matters(self):
        """The first parameter is the top of the stack"""
        got = []
        iface = SyscallInterface()
        iface.register(1, "pair", lambda a, b: got.append((a, b)) or 0, 2)
        iface.syscall([1], method="stack", stack=["b", "a"])
        self.assertEqual(got, [("a", "b")])


class Api(unittest.TestCase):
    def test_api_hides_the_number(self):
        """The wrapper finds the number by name"""
        iface, out = make()
        self.assertEqual(api_call(iface, "write", 1, "Greetings"), 9)
        self.assertEqual(api_call(iface, "getpid"), 1234)
        self.assertEqual(out, [(1, "Greetings")])

    def test_api_falls_back_to_block(self):
        """Too many arguments for registers: the wrapper uses a block"""
        iface, _ = make()
        self.assertEqual(api_call(iface, "sum7", 1, 1, 1, 1, 1, 1, 10), 16)

    def test_api_uses_registers_when_it_can(self):
        """Few arguments go in registers"""
        seen = []
        iface = SyscallInterface()
        original = iface.get_params

        def spy(method, *rest):
            seen.append(method)
            return original(method, *rest)

        iface.get_params = spy
        iface.register(1, "two", lambda a, b: a + b, 2)
        self.assertEqual(api_call(iface, "two", 2, 3), 5)
        self.assertEqual(seen, ["registers"])

    def test_register_limit_constant(self):
        """Five parameter registers"""
        self.assertEqual(NUM_PARAM_REGISTERS, 5)


if __name__ == "__main__":
    unittest.main()
