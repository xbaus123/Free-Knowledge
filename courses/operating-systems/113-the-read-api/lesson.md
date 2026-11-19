# An API Up Close: read()

*Chapter 2 · Part 3: System Calls.*

Let's read a real API entry. On UNIX and Linux you can look up any API function with the `man` command; `man read` describes `read()`:

```c
#include <unistd.h>

ssize_t   read(int fd, void *buf, size_t count)
   |        |    \______________________________/
return   function            parameters
value     name
```

## The pieces

A program that uses `read()` must **include the `unistd.h` header**, which defines the `ssize_t` and `size_t` data types (among other things).

| Parameter | Meaning |
|---|---|
| `int fd` | The **file descriptor** to read from: a small number the OS handed back when the file was opened |
| `void *buf` | A **buffer** where the data will be read into |
| `size_t count` | The **maximum number of bytes** to read into the buffer |

## The return value

| `read()` returns | It means |
|---|---|
| A positive number | That many bytes were read |
| `0` | **End of file**: nothing left to read |
| `-1` | **An error** occurred |

That's all a programmer needs. Nothing here says which trap instruction to use, which register holds what, or what number the kernel uses for `read`. The API hides it.

## A quick example

```c
char buf[100];
ssize_t n = read(fd, buf, 100);   // ask for up to 100 bytes
```

If the file has 40 bytes left, `n` is 40. Call it again and `n` is 0: end of file. If `fd` was never opened, `n` is -1.

A check on reading an API.
