# Mobile Structures: iOS and Android

*Chapter 2 · Part 7: Operating-System Structure.*

Phones run full operating systems with their own layered stacks.

## iOS

Apple's mobile OS for the iPhone and iPad.

- **Structured on Mac OS X**, with added functionality for mobile.
- **Does not run OS X applications natively**. It also runs on a **different CPU architecture**: ARM instead of Intel (Macs have since moved to ARM too).

Its layers, top to bottom:

| Layer | What it provides |
|---|---|
| **Cocoa Touch** | The **Objective-C API for developing apps** (touch, gestures, and so on; Swift today) |
| **Media services** | **Graphics, audio, video** |
| **Core services** | **Cloud computing, databases** |
| **Core OS** | The core operating system, **based on the Mac OS X kernel** |

## Android

- Developed by the **Open Handset Alliance (mostly Google)**, and **open source**.
- **A similar stack to iOS.**
- **Based on the Linux kernel, but modified**. The kernel provides **process, memory, and device-driver management**, and Android **adds power management**.

```
  +----------------------------------------------------+
  |               Application Framework                |
  +----------------------------------------------------+
  +---------------------------+  +---------------------+
  |        Libraries          |  |   Android runtime   |
  |  SQLite     openGL        |  |   Core Libraries    |
  |  surface    media         |  |                     |
  |  manager    framework     |  |  Dalvik virtual     |
  |  webkit     libc          |  |  machine            |
  +---------------------------+  +---------------------+
                 (modified Linux kernel below)
```

- The **runtime environment** includes a **core set of libraries** and the **Dalvik virtual machine**.
- **Apps are developed in Java plus the Android API.** Java class files are **compiled to Java bytecode, then translated to an executable that runs in the Dalvik VM**. (Newer Android versions replaced Dalvik with ART, the Android Runtime, which compiles ahead of time.)
- **Libraries** include frameworks for the **web browser (webkit)**, **database (SQLite)**, **multimedia**, and a **smaller libc**, since phones have less memory than desktops.

| | iOS | Android |
|---|---|---|
| Made by | Apple | Open Handset Alliance (mostly Google) |
| Source | Closed | **Open source** |
| Kernel | Based on the Mac OS X kernel | **Modified Linux** |
| App language and API | Objective-C, **Cocoa Touch** | **Java**, Android API |
| Apps run | Natively | In a **virtual machine** (Dalvik) |

A check on mobile structures.
