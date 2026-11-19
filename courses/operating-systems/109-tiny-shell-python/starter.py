"""A tiny command interpreter: built-in commands plus programs found by name."""

import posixpath

BUILTINS = {"cd", "pwd", "echo", "exit"}


class Shell:
    def __init__(self, programs=None):
        # Programs "on disk": a name -> a function that takes a list of
        # arguments and returns the program's output as a string.
        self.programs = dict(programs or {})
        self.cwd = "/"
        self.running = True

    def install(self, name, program):
        """Add a new program. Notice: the shell's code doesn't change."""
        self.programs[name] = program

    def parse(self, line):
        """Split a line into words on whitespace. A blank line, or one whose
        first non-space character is "#", gives []."""
        # TODO
        pass

    def change_dir(self, path):
        """Return the new current directory for `cd path`.
        No path means "/". A path starting with "/" is absolute; anything
        else is relative to self.cwd. Resolve "." and "..". You can't go
        above "/". The result never ends with "/" (except "/" itself)."""
        # TODO
        pass

    def execute(self, line):
        """Run one command line and return its output ("" if none).

        Built-ins (checked FIRST, before programs):
          cd [path]   -> set self.cwd with change_dir; output ""
          pwd         -> output self.cwd
          echo a b c  -> output "a b c"
          exit        -> set self.running to False; output ""
        Otherwise, if the command is in self.programs, call it with the
        arguments and return what it returns.
        Otherwise return "<command>: command not found".
        """
        # TODO
        pass

    def run_script(self, lines):
        """A batch interface: execute lines in order until one runs `exit`
        (or the lines run out). Return the list of non-empty outputs."""
        # TODO
        pass


if __name__ == "__main__":
    sh = Shell({"ls": lambda args: "Desktop  Documents  Music",
                "wc": lambda args: str(len(args))})
    print(sh.execute("pwd"))                  # /
    print(sh.execute("cd /Users/pbg/../amy")) # (nothing)
    print(sh.execute("pwd"))                  # /Users/amy
    print(sh.execute("echo  hello   world"))  # hello world
    print(sh.execute("ls"))                   # Desktop  Documents  Music
    print(sh.execute("grep x"))               # grep: command not found
    sh.install("grep", lambda args: "found " + args[0])
    print(sh.execute("grep x"))               # found x
