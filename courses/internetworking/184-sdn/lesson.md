# Software-Defined Networking

*Chapter 6 · Routing.*

At the start of this chapter, every router had its own control plane: its own routing processor running its own protocols. **Software-defined networking (SDN)** pulls the control plane **out of the boxes** and puts it in one place.

```
              ┌──────────────────────────────┐
              │  apps: firewall, load        │
              │  balancer, routing           │
              └──────────────┬───────────────┘
                 northbound API (REST)
              ┌──────────────┴───────────────┐
              │       SDN controller         │   control plane, centralized
              └──┬──────────┬────────────┬───┘
            southbound API (OpenFlow)
              ┌──┴──┐    ┌──┴──┐      ┌──┴──┐
              │ sw1 │────│ sw2 │──────│ sw3 │   data plane: "dumb" forwarding
              └─────┘    └─────┘      └─────┘
```

## How it works

- The **controller** is the central management point for the whole infrastructure. It computes the paths and the rules.
- It **instructs the data plane**: it installs **flow tables** in each switch: "packets matching *this* go out port 3," "packets matching *that* get dropped."
- The switches and routers can be **"dumb"**: they just match and forward. Even **ACLs** come from the controller.
- When a switch sees a packet that matches no rule, it asks the controller what to do.

The standard southbound protocol is **OpenFlow**. Controllers like **ONOS** and OpenDaylight run on Linux, and vendors build SDN control into their own operating systems, such as Cisco IOS XE.

## Why people like it

| Traditional | SDN |
|---|---|
| Configure each box by hand | Program the whole network from one place |
| Forwarding by destination address only | Match on almost any header field |
| New feature = new firmware from the vendor | New feature = new app on the controller |

## The catch

Putting all the control in one place makes that place:

- A **single point of failure**: if the controller is down, the network can't adapt.
- A **target**, on the order of a hypervisor (chapter 3): whoever controls it controls every switch.

The next reading looks at what attackers can do with that.

Next, a check on SDN.
