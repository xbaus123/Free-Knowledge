import unittest

from solution import KERNEL, USER, Machine, is_privileged


class Privileged(unittest.TestCase):
    def test_privileged(self):
        """Names in PRIVILEGED, with or without an argument"""
        for instr in ["set_timer", "io", "io:disk0", "disable_interrupts", "set_mode:0", "clear_memory", "halt"]:
            with self.subTest(instr=instr):
                self.assertTrue(is_privileged(instr))

    def test_not_privileged(self):
        """Ordinary instructions, traps, and system calls aren't"""
        for instr in ["add", "load", "store", "div0", "syscall:read", "syscall:io", "read_clock"]:
            with self.subTest(instr=instr):
                self.assertFalse(is_privileged(instr))


class Timer(unittest.TestCase):
    def test_boots_in_kernel_mode(self):
        """A new machine starts in kernel mode with no timer"""
        m = Machine()
        self.assertEqual(m.mode, KERNEL)
        self.assertEqual(m.timer, 0)
        self.assertEqual(m.log, [])

    def test_set_timer_in_kernel_mode(self):
        """The kernel can set the timer"""
        m = Machine()
        m.set_timer(5)
        self.assertEqual(m.timer, 5)

    def test_set_timer_in_user_mode(self):
        """Setting the timer is privileged"""
        m = Machine()
        m.mode = USER
        with self.assertRaises(PermissionError):
            m.set_timer(5)
        self.assertEqual(m.timer, 0)


class Running(unittest.TestCase):
    def test_reading_example(self):
        """The example from the lesson"""
        m = Machine()
        m.set_timer(3)
        self.assertEqual(m.run(["load", "syscall:write", "add", "add", "store"]), ("timer", 3))
        self.assertEqual(m.log, ["syscall:write", "interrupt:timer"])
        self.assertEqual(m.mode, KERNEL)

    def test_runs_to_completion(self):
        """No timer, no traps: the program finishes"""
        m = Machine()
        self.assertEqual(m.run(["load", "add", "store"]), ("done", 3))
        self.assertEqual(m.log, ["exit"])
        self.assertEqual(m.mode, KERNEL)

    def test_empty_program(self):
        """An empty program exits at once"""
        m = Machine()
        self.assertEqual(m.run([]), ("done", 0))
        self.assertEqual(m.log, ["exit"])

    def test_illegal_instruction(self):
        """A privileged instruction in user mode traps and kills the program"""
        m = Machine()
        self.assertEqual(m.run(["load", "io:disk0", "store"]), ("killed", 1))
        self.assertEqual(m.log, ["trap:illegal:io:disk0"])
        self.assertEqual(m.mode, KERNEL)

    def test_cant_turn_off_interrupts(self):
        """A program can't escape the timer by disabling interrupts"""
        m = Machine()
        m.set_timer(100)
        self.assertEqual(m.run(["disable_interrupts", "add"]), ("killed", 0))
        self.assertEqual(m.log, ["trap:illegal:disable_interrupts"])

    def test_divide_by_zero(self):
        """div0 traps"""
        m = Machine()
        self.assertEqual(m.run(["add", "add", "div0", "add"]), ("killed", 2))
        self.assertEqual(m.log, ["trap:divide-by-zero"])
        self.assertEqual(m.mode, KERNEL)

    def test_syscalls_run_in_kernel_mode(self):
        """handle_syscall is called in kernel mode, and user mode resumes after"""
        modes = []

        class Watched(Machine):
            def handle_syscall(self, name):
                modes.append((name, self.mode))
                super().handle_syscall(name)

        m = Watched()
        self.assertEqual(m.run(["syscall:open", "add", "syscall:read", "syscall:close"]), ("done", 4))
        self.assertEqual(modes, [("open", KERNEL), ("read", KERNEL), ("close", KERNEL)])
        self.assertEqual(m.log, ["syscall:open", "syscall:read", "syscall:close", "exit"])

    def test_user_mode_between_syscalls(self):
        """After a system call returns, the program is back in user mode"""
        m = Machine()
        # a privileged instruction right after a system call must still trap
        self.assertEqual(m.run(["syscall:a", "io"]), ("killed", 1))
        self.assertEqual(m.log, ["syscall:a", "trap:illegal:io"])
        self.assertEqual(m.mode, KERNEL)

    def test_infinite_loop_is_stopped(self):
        """The timer stops a program that would never stop"""
        m = Machine()
        m.set_timer(1000)
        forever = ["add"] * 10_000
        self.assertEqual(m.run(forever), ("timer", 1000))
        self.assertEqual(m.log, ["interrupt:timer"])
        self.assertEqual(m.timer, 0)

    def test_timer_counts_syscalls(self):
        """System calls are completed instructions too"""
        m = Machine()
        m.set_timer(2)
        self.assertEqual(m.run(["syscall:a", "syscall:b", "syscall:c"]), ("timer", 2))
        self.assertEqual(m.log, ["syscall:a", "syscall:b", "interrupt:timer"])

    def test_program_ends_before_timer(self):
        """A short program finishes before the timer goes off"""
        m = Machine()
        m.set_timer(10)
        self.assertEqual(m.run(["add", "add"]), ("done", 2))
        self.assertEqual(m.timer, 8)

    def test_run_needs_kernel_mode(self):
        """Only the kernel can start a program"""
        m = Machine()
        m.mode = USER
        with self.assertRaises(PermissionError):
            m.run(["add"])

    def test_back_to_back(self):
        """The kernel can run one program after another"""
        m = Machine()
        m.set_timer(2)
        self.assertEqual(m.run(["add"] * 5), ("timer", 2))
        m.set_timer(2)
        self.assertEqual(m.run(["add"]), ("done", 1))
        self.assertEqual(m.log, ["interrupt:timer", "exit"])


if __name__ == "__main__":
    unittest.main()
