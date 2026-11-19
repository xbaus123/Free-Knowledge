# Windows and UNIX Side by Side

*Chapter 2 · Part 4: Types of System Calls.*

Our names have been generic. Here's what real systems call them:

| Category | Windows | UNIX |
|---|---|---|
| **Process control** | `CreateProcess()` | `fork()` |
| | `ExitProcess()` | `exit()` |
| | `WaitForSingleObject()` | `wait()` |
| **File manipulation** | `CreateFile()` | `open()` |
| | `ReadFile()` | `read()` |
| | `WriteFile()` | `write()` |
| | `CloseHandle()` | `close()` |
| **Device manipulation** | `SetConsoleMode()` | `ioctl()` |
| | `ReadConsole()` | `read()` |
| | `WriteConsole()` | `write()` |
| **Information maintenance** | `GetCurrentProcessID()` | `getpid()` |
| | `SetTimer()` | `alarm()` |
| | `Sleep()` | `sleep()` |
| **Communications** | `CreatePipe()` | `pipe()` |
| | `CreateFileMapping()` | `shmget()` |
| | `MapViewOfFile()` | `mmap()` |
| **Protection** | `SetFileSecurity()` | `chmod()` |
| | `InitializeSecurityDescriptor()` | `umask()` |
| | `SetSecurityDescriptorGroup()` | `chown()` |

## Things to notice

- **Windows names are long and descriptive** (`CreateProcess`); **UNIX names are short** (`fork`).
- **UNIX uses `read()` and `write()` for both files and devices.** Windows has separate `ReadFile()` and `ReadConsole()`. That's the "files and devices merged" idea from two lessons ago.
- **`ioctl()`** ("I/O control") is UNIX's catch-all for device settings.
- **`pipe()`** creates a one-way channel between processes (message passing). **`shmget()`** and **`mmap()`** set up shared memory.
- **`chmod()`** changes a file's permissions, **`chown()`** its owner, and **`umask()`** the default permissions for new files.

You don't need to memorize every row. Being able to look at a name and guess its category is the useful skill, and the next check practises exactly that.
