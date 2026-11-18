# Storage Management

*Chapter 1 · Part 5: Resource Management.*

Disks, SSDs, USB sticks, and network drives all store data differently. Programs shouldn't need to care. The OS gives them **one uniform, logical view of information storage**.

## The file

The OS **abstracts** the physical properties of its storage devices into a **logical storage unit: the file**.

A file is just a named collection of related information. You open `report.txt` the same way whether it lives on an SSD, a spinning hard disk, or a server across the room. The OS **maps files onto the physical media** behind the scenes.

## Devices differ

Each storage medium is controlled by a device (a disk drive, a tape drive), and they vary a lot:

| Property | Examples |
|---|---|
| **Access speed** | Nanoseconds for memory; milliseconds for a hard disk |
| **Capacity** | Megabytes on old media; terabytes on a modern disk |
| **Data-transfer rate** | MB/s to GB/s |
| **Access method** | **Sequential** (tape: read in order) or **random** (disk: jump anywhere) |

The file abstraction hides all of that.

## File-system management

Files are usually organized into **directories** (folders), and most systems have **access control** to determine **who can access what**: who can read a file, write it, or run it.

The OS's file-system activities include:

1. **Creating and deleting files** and directories.
2. Providing **primitives to manipulate** files and directories (open, read, write, rename, move).
3. **Mapping files onto secondary storage**: deciding which blocks on the disk hold each file.
4. **Backing up files** onto stable (nonvolatile) storage media.

Next, a check on storage management.
