# Protection and Security

*Chapter 1 · Part 6: Protection, Security, and Kernel Data Structures.*

A computer with many users and many processes needs rules about **who can touch what**. Two words cover this, and they mean different things.

## Two definitions

- **Protection**: **any mechanism for controlling the access of processes or users to the resources defined by the OS**: files, memory, the CPU, devices. Dual mode, the timer, and file permissions are all protection mechanisms.
- **Security**: **defense of the system against internal and external attacks**. That's a **huge range**: **denial-of-service**, **worms**, **viruses**, **identity theft**, and **theft of service** (using a system without paying or without permission).

Protection is the machinery; security is the defense of the whole system. A system can have perfect protection and still be insecure: if an attacker steals your password, the OS will faithfully protect your files... for the attacker.

## First: who are you?

Systems generally **first distinguish among users**, to determine **who can do what**.

- **User identities** (**user IDs**, or security IDs on Windows) include a **name and an associated number**, **one per user**.
- That **user ID is then associated with all files and processes** of that user, to determine **access control**. Every file you create and every program you run is tagged with your ID.

## Groups

- A **group identifier** (**group ID**) allows a **set of users** to be defined and controls managed for the whole set. The group ID is **also associated with each process and file**.
- Example: every student in a course belongs to the group `os101`, and the course folder is readable by that group.

## Privilege escalation

Sometimes a user needs **more rights** for a moment: installing software, changing a system setting. **Privilege escalation** allows a user to **change to an effective ID with more rights**.

On UNIX, `sudo` runs a single command as the administrator (root), after checking you're allowed to. The danger: if an attacker finds a way to escalate privilege, they get those rights too. Many real attacks are exactly that.

```
 $ id
 uid=501(alex) gid=20(staff) groups=20(staff),80(admin)
 $ sudo whoami
 root
```

Next, a check on protection and security.
