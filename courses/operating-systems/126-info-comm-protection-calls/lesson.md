# Information, Communication, and Protection Calls

*Chapter 2 · Part 4: Types of System Calls.*

The last three categories.

## Information maintenance

Calls that **move information between the program and the OS**:

- **get time or date, set time or date**
- **get system data, set system data** (the number of current users, the OS version, free memory or disk space)
- **get and set process, file, or device attributes**

## Communications

Remember the two models of communication from Part 1? Each has its own calls.

**Message-passing model.** Processes exchange **messages**, either directly or through a shared mailbox.

- **create, delete communication connection**: before talking, you open a connection. The other end is named by a **host name** (which computer) and a **process name** (which process on it).
- **send, receive messages**: typically from a **client** to a **server**. The server is a process (often a daemon, as Part 5 explains) waiting for connections.

**Shared-memory model.** Processes **create and gain access to memory regions** owned by other processes. Normally the OS stops one process from touching another's memory; with shared memory, the processes agree to remove that restriction for one region.

Both models also have:

- **transfer status information**
- **attach and detach remote devices**

| | Message passing | Shared memory |
|---|---|---|
| Good for | Smaller amounts of data; works easily between computers | Speed and convenience on one computer |
| Watch out for | Every message goes through the OS | The processes must make sure they don't write the same location at once |

## Protection

Protection calls **control access to resources**:

- **get and set permissions** (on files, devices, and more)
- **allow and deny user access**

Protection used to matter only on multiuser machines. Now that every computer is on a network, every OS needs it.

A check on the last three categories.
