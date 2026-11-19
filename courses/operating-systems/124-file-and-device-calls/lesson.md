# File and Device System Calls

*Chapter 2 · Part 4: Types of System Calls.*

Two categories that look surprisingly alike.

## File management

| Calls | What they're for |
|---|---|
| **create file, delete file** | Make a new file; remove one |
| **open, close** | Start using a file; finish with it |
| **read, write, reposition** | Move data in or out; jump to a different spot in the file (rewind, skip ahead) |
| **get / set file attributes** | File name, type, protection codes, size, and so on |

The file-copy program from Part 3 used nearly every one of these.

## Device management

A process may need resources to do its work: more memory, a disk drive, a camera. Any resource the OS controls can be thought of as a **device**.

| Calls | What they're for |
|---|---|
| **request device, release device** | Get exclusive use of a device; give it back |
| **read, write, reposition** | Same as for files |
| **get / set device attributes** | Read or change a device's settings |
| **logically attach or detach devices** | Connect or disconnect a device from the system |

## Why they look the same

Notice that **read, write, and reposition** appear in *both* lists. The similarity is so strong that many operating systems, including **UNIX**, **merge files and devices into one structure**. In UNIX, a device shows up as a special file (like `/dev/tty` or `/dev/sda`), and you use the same `open`, `read`, `write`, and `close` calls on it.

**request and release** are like **open and close** for devices: a process has to get a device before using it, and release it afterward so another process can have it. If the device is busy, the process may have to **wait**.

A check on files and devices.
