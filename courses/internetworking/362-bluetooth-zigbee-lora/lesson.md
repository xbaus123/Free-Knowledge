# Bluetooth, Zigbee, and LoRa

*Chapter 11 · Wireless and IoT.*

A door sensor might run on one battery for five years. Wi-Fi would drain that battery in weeks. **Low-power networks** trade speed for battery life, and they're how most IoT devices talk.

## Bluetooth

- **2.4 GHz**, like Wi-Fi, but at much **lower power**, so the distance is limited: typically about 10 meters.
- **Small scale**: a Bluetooth network (a *piconet*) has one central device and at most **7 active** devices connected to it.
- Generally **peer-to-peer**: phone to headphones, laptop to mouse.
- It uses **FHSS**, from the spread spectrum reading.

**How pairing works:**

1. **Enable** pairing, so the device is discoverable.
2. The other device **scans** and finds it.
3. **Connect and authenticate**, often by confirming a matching code on both screens.
4. **Bond**: both devices save the keys.
5. **Auto-connect** in the future using the saved keys, with no pairing needed.

## Zigbee

- A low-power **mesh** for home and building automation: smart bulbs, locks, thermostats, sensors. Mains-powered devices relay messages for the others.
- **250 kbps** maximum data rate, which is plenty for "turn the light on."
- Radio bands: **2.4 GHz** worldwide, plus lower bands in some regions: **915 MHz** in the Americas, **868 MHz** in Europe, and **784 MHz** in China.
- On 2.4 GHz, Zigbee **shares the band with Wi-Fi**, so the two can interfere. Put Zigbee on channels that fall between your busy Wi-Fi channels.

## LoRa

- **LoRa** (**Long Range**) uses low-frequency radio (915 MHz in the US, 868 MHz in Europe) to reach **kilometers**, from a few in a city to 15 or more in open country, on years of battery.
- It spreads its signal with yet another technique, **chirp spread spectrum**: a tone that sweeps up through the band.
- The price is size and speed: a packet carries about **256 bytes at most**, slowly.
- Used for IoT that's spread out: farm and soil sensors, utility meters, asset trackers, and **medical devices** like remote patient monitors. **LoRaWAN** is the network protocol built on it.

## Side by side

| | Wi-Fi | Bluetooth | Zigbee | LoRa |
|---|---|---|---|---|
| Range | Building | About 10 m | Building, via mesh | Kilometers |
| Speed | Hundreds of Mbps or more | A few Mbps at most | 250 kbps | A few kbps or less |
| Power | High | Low | Very low | Very low |
| Shape | Star around a WAP | Peer-to-peer, up to 7 devices | Mesh | Star around a gateway |
| Typical use | Laptops, phones | Headphones, wearables | Smart home | Remote sensors |

Next, a check on low-power networks.
