# A System-Call Table in Python

*Chapter 2 · Part 3: System Calls.*

Now build the machinery from the last two lessons: a **system-call interface** with a table of numbered calls, the **three ways to pass parameters**, and a **library wrapper** that hides it all.

## The setup

A trap is modelled as `syscall(regs, ...)`. `regs` is a list of register values: **`regs[0]` holds the system-call number**, and `regs[1]` onward can hold parameters. `NUM_PARAM_REGISTERS` is `5`, so `r1` to `r5` are available.

A system call's **handler** is a Python function; `nparams` says how many parameters it takes.

## Your task

1. **`register(number, name, handler, nparams)`**: add an entry to `self.table` as `number -> (name, handler, nparams)`. Raise `ValueError` if the number or the name is already taken.
2. **`number_of(name)`**: find a call's number by name, or raise `KeyError`.
3. **`get_params(method, nparams, regs, memory, stack)`**: collect the parameters, **first parameter first**:
   - `"registers"`: `regs[1]`, `regs[2]`, … Raise `ValueError` if `nparams` is more than `NUM_PARAM_REGISTERS`.
   - `"block"`: `regs[1]` holds an address `X`; the parameters are `memory[X]`, `memory[X+1]`, …
   - `"stack"`: the program **pushed the parameters last-first** (the end of the list is the top), so **popping** gives the first one first. Really pop them; the stack shrinks.
   - Anything else: `ValueError`.
4. **`syscall(regs, method="registers", memory=None, stack=None)`**: look up `regs[0]`. Unknown number: return `-1`. Otherwise collect the parameters and return `handler(*params)`.
5. **`api_call(iface, name, *args)`**: the **library wrapper**, like `printf` calling `write`. Look up the number by name and make the call with the arguments in registers. If there are more arguments than registers, fall back to the **block** method: put the arguments in a new list and pass address `0`.

## An example

```python
iface = SyscallInterface()
iface.register(4, "write", lambda fd, text: len(text), 2)
iface.syscall([4, 1, "hi"])                                        # 2  (registers)
iface.syscall([4, 7], method="block", memory=[0]*7 + [1, "yo"])    # 2  (block at address 7)
iface.syscall([4], method="stack", stack=["abc", 1])               # 3  (pops 1, then "abc")
api_call(iface, "write", 1, "Greetings")                           # 9
```

Notice who knows what: the caller of `api_call` never sees the number `4`.

Use **Run** to try things out, and **Submit** to run the tests.
