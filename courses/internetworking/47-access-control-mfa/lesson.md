# Access Control and Multi-Factor Authentication

*Chapter 2 · Topologies and the Physical Layer.*

A card reader on a door and a login screen on a server answer the same two questions:

1. **Authentication**: *who are you?* Prove your identity.
2. **Authorization**: *what are you allowed to do?* Now that we know who you are, decide which doors, rooms, and systems you get.

Authentication always comes first. You can't decide what someone may do until you know who they are.

## The three authentication factors

Every way of proving who you are falls into one of three **factors**:

| Factor | Examples |
|---|---|
| **Something you know** | A password, a PIN, the answer to a security question |
| **Something you have** | An ID **card**, a security **token** or key fob, a phone running an authenticator app |
| **Something you are** | **Biometrics**: fingerprint, face, iris, voice |

## Multi-factor authentication (MFA)

**MFA** requires **at least two different factors**. The usual rule: **pick 2** (or more) from the three.

The point is that each factor fails in a different way. A password can be guessed or phished, a card can be stolen, and a fingerprint can't be changed once copied. An attacker who has one factor still doesn't have the other.

The factors have to be **different kinds**. A password plus a PIN is still *two things you know*, so it's not MFA: one phishing page can collect both.

| Combination | MFA? | Why |
|---|---|---|
| Badge + PIN on the door's touchpad | Yes | Have + know |
| Password + code from a phone app | Yes | Know + have |
| Fingerprint + badge | Yes | Are + have |
| Password + security question | **No** | Know + know |
| Two different badges | **No** | Have + have |

## Authorization schemes

Once someone is authenticated, an **authorization scheme** decides what they get. A few common approaches:

- **By role**: everyone in the "network admin" role can open the server room. Easy to manage, since you change the role, not every person.
- **By need to know**: you get access only to what your current job requires, and nothing more. This is the idea of **least privilege**.
- **By rule**: access depends on conditions, like "only during business hours" or "only from inside the building".

## Tripwires: noticing when it fails anyway

Locks and logins can be bypassed, so good security also **detects** intrusions. A **tripwire** is anything that raises an alarm when something it watches changes:

- **Physically**: door sensors, motion detectors, a rack door alarm.
- **Digitally**: software that keeps fingerprints of important files and alerts when one changes, or an alarm when an unknown device appears on the network.

Prevent what you can, detect what you can't, and respond quickly when the alarm goes off.

Next, a check on authentication, MFA, and authorization.
