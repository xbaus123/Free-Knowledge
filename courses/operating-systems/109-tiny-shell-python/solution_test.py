import unittest

from solution import Shell


def make():
    return Shell({
        "ls": lambda args: "Desktop  Documents  Music",
        "wc": lambda args: str(len(args)),
        "cat": lambda args: "|".join(args),
    })


class Parsing(unittest.TestCase):
    def test_words(self):
        """Lines split on any whitespace"""
        self.assertEqual(make().parse("  ls   -l\t/tmp "), ["ls", "-l", "/tmp"])

    def test_blank_and_comments(self):
        """Blank lines and comments give no words"""
        sh = make()
        for line in ["", "   ", "# a comment", "   # indented comment"]:
            with self.subTest(line=line):
                self.assertEqual(sh.parse(line), [])


class ChangeDir(unittest.TestCase):
    def check(self, cwd, path, expected):
        sh = make()
        sh.cwd = cwd
        self.assertEqual(sh.change_dir(path), expected)

    def test_absolute(self):
        """An absolute path ignores the current directory"""
        self.check("/home", "/usr/bin", "/usr/bin")

    def test_relative(self):
        """A relative path starts at the current directory"""
        self.check("/home", "amy", "/home/amy")
        self.check("/", "etc", "/etc")

    def test_dot_and_dotdot(self):
        """. stays put and .. goes up"""
        self.check("/home/amy", "..", "/home")
        self.check("/home/amy", "./docs/../music/.", "/home/amy/music")
        self.check("/Users", "/Users/pbg/../amy", "/Users/amy")

    def test_cant_go_above_root(self):
        """.. at the root stays at the root"""
        self.check("/", "..", "/")
        self.check("/a", "../../../b", "/b")

    def test_no_path_goes_root(self):
        """cd with no argument goes to /"""
        self.check("/home/amy", None, "/")

    def test_trailing_slashes(self):
        """Extra slashes are ignored"""
        self.check("/", "usr//local/", "/usr/local")


class Builtins(unittest.TestCase):
    def test_pwd_starts_at_root(self):
        """A new shell starts in /"""
        self.assertEqual(make().execute("pwd"), "/")

    def test_cd_then_pwd(self):
        """cd changes the shell's own state"""
        sh = make()
        self.assertEqual(sh.execute("cd /Users/pbg"), "")
        self.assertEqual(sh.execute("pwd"), "/Users/pbg")
        sh.execute("cd ..")
        self.assertEqual(sh.execute("pwd"), "/Users")
        sh.execute("cd")
        self.assertEqual(sh.execute("pwd"), "/")

    def test_echo(self):
        """echo joins its arguments with single spaces"""
        self.assertEqual(make().execute("echo  hello   world"), "hello world")
        self.assertEqual(make().execute("echo"), "")

    def test_exit(self):
        """exit stops the shell"""
        sh = make()
        self.assertTrue(sh.running)
        self.assertEqual(sh.execute("exit"), "")
        self.assertFalse(sh.running)

    def test_builtins_win(self):
        """A built-in is found before a program with the same name"""
        sh = make()
        sh.install("echo", lambda args: "the echo program")
        sh.install("pwd", lambda args: "the pwd program")
        self.assertEqual(sh.execute("echo hi"), "hi")
        self.assertEqual(sh.execute("pwd"), "/")


class Programs(unittest.TestCase):
    def test_runs_program_with_args(self):
        """Programs get the arguments after the command name"""
        sh = make()
        self.assertEqual(sh.execute("ls"), "Desktop  Documents  Music")
        self.assertEqual(sh.execute("wc a b c"), "3")
        self.assertEqual(sh.execute("cat x y"), "x|y")

    def test_not_found(self):
        """Unknown commands are reported"""
        self.assertEqual(make().execute("grep foo"), "grep: command not found")

    def test_install_new_program(self):
        """Adding a program doesn't need a new shell"""
        sh = make()
        self.assertEqual(sh.execute("hello"), "hello: command not found")
        sh.install("hello", lambda args: "hi " + " ".join(args))
        self.assertEqual(sh.execute("hello amy"), "hi amy")

    def test_blank_line(self):
        """A blank line or comment does nothing"""
        sh = make()
        self.assertEqual(sh.execute(""), "")
        self.assertEqual(sh.execute("# ls"), "")
        self.assertTrue(sh.running)


class Scripts(unittest.TestCase):
    def test_script(self):
        """A batch script runs every line"""
        out = make().run_script(["cd /tmp", "pwd", "# comment", "echo done", "wc 1 2"])
        self.assertEqual(out, ["/tmp", "done", "2"])

    def test_script_stops_at_exit(self):
        """Nothing runs after exit"""
        sh = make()
        out = sh.run_script(["echo one", "exit", "echo two", "cd /nowhere"])
        self.assertEqual(out, ["one"])
        self.assertEqual(sh.cwd, "/")
        self.assertFalse(sh.running)

    def test_empty_script(self):
        """An empty script has no output"""
        self.assertEqual(make().run_script([]), [])


if __name__ == "__main__":
    unittest.main()
