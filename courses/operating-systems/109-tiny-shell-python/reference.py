"""A tiny command interpreter: built-in commands plus programs found by name."""

import posixpath

BUILTINS = {"cd", "pwd", "echo", "exit"}


class Shell:
    def __init__(self, programs=None):
        self.programs = dict(programs or {})
        self.cwd = "/"
        self.running = True

    def install(self, name, program):
        self.programs[name] = program

    def parse(self, line):
        if line.strip().startswith("#"):
            return []
        return line.split()

    def change_dir(self, path):
        if not path:
            return "/"
        if not path.startswith("/"):
            path = self.cwd.rstrip("/") + "/" + path
        parts = []
        for part in path.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                if parts:
                    parts.pop()
            else:
                parts.append(part)
        return "/" + "/".join(parts)

    def execute(self, line):
        words = self.parse(line)
        if not words:
            return ""
        cmd, args = words[0], words[1:]
        if cmd == "cd":
            self.cwd = self.change_dir(args[0] if args else None)
            return ""
        if cmd == "pwd":
            return self.cwd
        if cmd == "echo":
            return " ".join(args)
        if cmd == "exit":
            self.running = False
            return ""
        if cmd in self.programs:
            return self.programs[cmd](args)
        return f"{cmd}: command not found"

    def run_script(self, lines):
        out = []
        for line in lines:
            result = self.execute(line)
            if result:
                out.append(result)
            if not self.running:
                break
        return out
