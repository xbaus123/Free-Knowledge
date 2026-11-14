# SIP: Setting Up Calls

*Chapter 9 · Upper Layers.*

**SIP**, the **Session Initiation Protocol**, is the textbook session-layer protocol. It's defined in **RFC 3261** and it sets up, changes, and ends voice and video calls. Office VoIP phones use it, and so do the gateways that connect Microsoft Teams and Zoom to the phone network and to meeting-room systems.

SIP **does not carry the audio or video itself**. It handles the session, and other protocols (usually **RTP**) carry the media. That split is exactly the OSI idea: the session layer manages the conversation, not the content.

## How a call works

1. **Register.** Each phone or app logs in to a SIP server (the **registrar**): "I'm `sip:bob@example.com`, and right now I'm at this IP address."
2. **Invite.** Alice calls Bob. Her app sends an **INVITE** to the SIP server, which forwards it to Bob's device. The INVITE carries the **specifications** for the call: which codecs, which IP addresses and ports to send media to. (In a meeting link, these details are usually packed into the link.)
3. **Ringing and answer.** Bob's device replies **180 Ringing**, then **200 OK** when he picks up. Alice's app confirms with **ACK**.
4. **Active communication.** Audio and video now flow directly between the two devices over **RTP**. SIP stays quiet.
5. **Termination.** Whoever hangs up sends **BYE**, and the other side answers **200 OK**.

```
Alice                 SIP server                 Bob
  | --- INVITE ----------> | --- INVITE ----------> |
  | <-- 100 Trying ------- |                        |
  | <-- 180 Ringing ------ | <-- 180 Ringing ------ |
  | <-- 200 OK ----------- | <-- 200 OK ----------- |
  | --- ACK -------------------------------------> |
  | <============ RTP audio and video ===========> |
  | --- BYE -------------------------------------> |
  | <-- 200 OK ----------------------------------- |
```

## It looks like HTTP

SIP is **text-based** and was modeled on HTTP, which you'll meet later in this chapter. Its replies even use HTTP-style codes: **1xx** for "working on it", **2xx** for success, **4xx** for the caller's problem (**404** no such user, **486 Busy Here**).

SIP normally uses port **5060** (UDP or TCP), and **5061** for SIP over TLS.

Next, a check on SIP.
