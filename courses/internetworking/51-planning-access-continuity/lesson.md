# Planning the Physical Layer: Devices, Access, and Continuity

*Chapter 2 · Topologies and the Physical Layer.*

With the site chosen and the space fitted out, the last two groups of planning questions are about what goes on the network, who can reach it, and how it survives when something goes wrong.

## 3. Devices and access

- **What's on the network**: **clients**, **servers**, and **network devices** (switches, routers, access points).
- **User access on-site**: How do people prove who they are? **Username and password**, a **token**, **biometrics**, or a combination (MFA).
- **Remote access**: People working from home need a **VPN** (virtual private network), an encrypted tunnel into the network. A **hardware VPN** is a dedicated device at the network's edge: fast and good for connecting whole offices. A **software VPN** runs as an app on each laptop or phone: cheap and flexible for individual users.

## 4. Support and continuity

- **The workspace**: where the people who run the network sit, and where the **hubs** and **cabling** for their area go.
- **Service provider access**: how your ISP's line enters the building, and whether you have a second provider in case the first goes down.
- **Backup**: copies of the data, **on-site** (fast to restore) or **remote** (survives a fire or flood at the site). The usual answer is both.
- **Storage and archives**: where data lives day to day, and where old data is kept, for how long.

## Think in systems terms

A good plan describes the network as a **system**:

- **Elements**: the parts (clients, servers, switches, cables, rooms, people).
- **Functions**: what each part does (stores files, routes traffic, authenticates users).
- **Interconnections**: how the parts connect (which cable, which topology, which path through the building).

If you can list all three, you can draw the network, and if you can draw it, you can find its weak spots.

## Try it yourself

Sketch a plan for a small company's network, in systems terms. Give it:

- A **WAN**: at least two sites connected to each other.
- Support for **50 or more users**.
- **Remote access** for employees working from home.
- Access for **partners or customers**.
- **Important assets** worth protecting, like financial records or customer data.

Then switch sides: you're an attacker. Where's the easiest place to break in, physically or over the network? Fix that, and look again.

Next, a check on devices, access, and continuity.
