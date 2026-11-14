# What Email Is

*Chapter 8 · Mail.*

Email is an **asynchronous message exchange service**. That one phrase explains most of how it's built.

## Asynchronous

A phone call is **synchronous**: both people have to be there at the same moment. Email isn't. You send when you like, the other person reads when they like, and neither of you has to be online when the other one is. Somewhere in between, the message **waits**.

That waiting happens on **servers**, which is why email is a **client-server** system. Your laptop or phone (the client) hands a message to a server, and servers pass it along until it reaches a server that holds the recipient's mailbox. The recipient's client collects it later.

## It uses TCP, ironically

You might expect a "send it and it'll get there eventually" service to use UDP. It doesn't: every hop is a **TCP** connection. The irony is only on the surface:

- **Each hop** is a live, reliable conversation. The sending server connects, the receiving server confirms every step, and the message isn't considered handed over until the receiver says so.
- **End to end**, the delivery is asynchronous. If the next server is down, the current one keeps the message and tries again later.

Reliable hops, chained together with patient waiting, give you a service that almost never loses mail even though the recipient's server was unreachable at the moment you hit send.

## It depends on DNS

Mail can't go anywhere without the **name service** from chapter 7. An address like `alice@example.com` doesn't contain an IP address. The sending server has to ask DNS "who takes mail for `example.com`?" (the **MX** record) and then "what's that host's address?" (its **A** record). If DNS is broken, mail stops.

## The problems that come with it

Email was designed in the 1970s and 80s for a small network of people who trusted each other. That leaves three big issues:

- **Hacking**: mail servers face the whole Internet, and email is the most common way attackers get in, through phishing.
- **Attachments**: any file can ride along, including malware.
- **Privacy**: the original protocols send everything, passwords included, as plain text.

## Who's it for?

When you plan mail for a network, there are two audiences:

- **Your users**, inside the organization: staff sending to each other and to the world.
- **Customers**, outside: people who need to reach you, and automated mail you send them (receipts, password resets).

They have different needs, and later in the chapter you'll plan for both.

Next, a check on what makes email email.
