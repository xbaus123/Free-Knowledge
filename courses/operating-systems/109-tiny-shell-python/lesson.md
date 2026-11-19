# A Tiny Shell in Python

*Chapter 2 · Part 2: User Interfaces.*

Time to build a command interpreter. Yours will have a few **built-in** commands and run everything else as a **program found by name**, exactly the split from the CLI lesson.

## The pieces

`Shell` holds:

- `programs`: the programs "on disk", a dict from a name to a Python function. A program takes a **list of arguments** and returns its output as a string.
- `cwd`: the current directory, starting at `"/"`.
- `running`: `True` until someone types `exit`.

`install(name, program)` is written for you. It adds a program **without changing the shell's code**, which is the whole point of the program-name approach.

## Your task

1. **`parse(line)`**: split on whitespace. A blank line, or one whose first non-space character is `#`, gives `[]`.
2. **`change_dir(path)`**: work out where `cd path` lands.
   - No path (`None`) means `"/"`.
   - A path starting with `/` is absolute. Anything else is relative to `cwd`.
   - Skip empty parts and `.`; `..` goes up one level, but never above `/`.
   - Return a clean path like `"/home/amy"`, never with a trailing slash (except `"/"` itself).
3. **`execute(line)`**: run one command and return its output (`""` if there isn't any).
   - **Built-ins are checked first**: `cd`, `pwd`, `echo` (joins its arguments with single spaces), and `exit` (sets `running` to `False`).
   - Otherwise, if the command names a program, call it with the remaining words and return its result.
   - Otherwise return `"<command>: command not found"`.
4. **`run_script(lines)`**: a **batch** interface. Execute the lines in order, stopping right after one runs `exit`. Return the list of **non-empty** outputs.

## An example

```python
sh = Shell({"ls": lambda args: "Desktop  Documents"})
sh.execute("cd /Users/pbg/../amy")   # ""
sh.execute("pwd")                    # "/Users/amy"
sh.execute("grep x")                 # "grep: command not found"
sh.install("grep", lambda args: "found " + args[0])
sh.execute("grep x")                 # "found x"
```

Notice why `cd` is a built-in: it changes `sh.cwd`, the shell's own state. A program function only gets its arguments, so it couldn't.

Use **Run** to try things out, and **Submit** to run the tests.
