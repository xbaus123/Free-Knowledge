# Securing IoT Devices

*Chapter 11 · Wireless and IoT.*

IoT devices are everywhere on modern networks, and they're some of the hardest devices to secure.

## What makes IoT different

- **Simple.** Many do one thing: turn on and off, or report a reading.
- **Low memory and limited processing.** No room for antivirus, and often too little power for strong authentication. That makes them **hard to authenticate**.
- **Paired with sensors.** **Sensors** are how IoT collects information: temperature, motion, a door opening, a heart rate.
- **Long-lived and rarely patched.** A camera may run the same firmware for ten years, often with its **default password** unchanged.

That last point has already caused real damage. In 2016, the **Mirai** botnet took over hundreds of thousands of cameras and routers using lists of default passwords, and used them to flood the DNS provider Dyn. For hours, sites like Twitter and Netflix couldn't be reached by name (chapter 7).

## Give IoT its own network segment

Put IoT devices on their **own segment**: their own VLAN and subnet (chapters 3 and 5), and their own SSID. Then use firewall rules so each device can reach **only** what it needs, like its controller or its vendor's service, and **never** staff laptops or servers. If a camera is taken over, the attacker is stuck in the IoT segment.

The same goes for Wi-Fi in general: wireless networks **should** sit on their own segments, separate from the wired core. It isn't required, but it's good practice.

## Profile the sensor: "known good"

Because an IoT device does so little, its normal behavior is very predictable: which hosts it talks to, how often, and how much. Record that as its **known good** profile, the same idea as chapter 10's baselines, and alert on anything different.

A thermostat that has sent 2 KB to its vendor every 10 minutes for a year, and suddenly starts scanning the network or talking to an unknown server overseas, has almost certainly been taken over.

## The checklist

1. **Change default passwords** before the device goes on the network.
2. **Update firmware**, from the vendor, after checking its signature (chapter 10).
3. **Segment**: its own VLAN, subnet, and SSID, with tight firewall rules.
4. **Profile** known-good behavior, and alert on changes.
5. **Turn off** features you don't use, like remote access and Universal Plug and Play (UPnP).

## Wrapping up Wi-Fi

Wi-Fi is **asynchronous** by nature: devices contend for the air whenever they have something to send, instead of getting guaranteed slots. That makes it **slower**, less predictable, and **harder to authenticate**, since anyone in range can try. IoT adds devices with **limited processing**, which makes authentication harder still, and **sensors**, which are how IoT collects its information.

Next, a check on securing IoT.
