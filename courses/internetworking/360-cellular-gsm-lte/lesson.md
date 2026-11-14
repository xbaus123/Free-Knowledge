# Cellular: GSM and LTE

*Chapter 11 · Wireless and IoT.*

Wi-Fi covers a building. **Cellular** networks cover a country. The area is divided into **cells**, each served by a tower. Neighboring cells use different frequencies, and cells far apart reuse them: the same **frequency reuse** as Wi-Fi channels, on a much bigger scale.

## GSM

**GSM**, the **Global System for Mobile Communications**, was the standard 2G system, launched in 1991 and still the base that later generations grew from.

- It uses **TDMA** (chapter 3): each 200 kHz carrier is cut into **8 time slots**, so eight calls share one carrier.
- It introduced the **SIM card**, which holds the subscriber's identity and secret key. Move the SIM to another phone, and your number comes with it.

## How GSM works

| Part | Short name | Job |
|---|---|---|
| **Mobile Station** | MS | The phone, plus the **SIM card** with the subscriber's info |
| **Base Transceiver Station** | BTS | The **cell tower**: manages radio communication with the phones in its cell |
| **Base Station Controller** | BSC | Controls **multiple BTS units**: assigns radio channels, and hands calls from one tower to the next |
| **Base Station Subsystem** | BSS | The BTSs and their BSC together: manages the radio connection between the phones and the **core network** |

```
 [phone + SIM] )))  [BTS] --+
 [phone + SIM] )))  [BTS] --+-- [BSC] -- core network -- phone network, Internet
                    [BTS] --+
                   |<---- BSS ---->|
```

## LTE

**LTE** (**Long Term Evolution**) is the **4G** standard, widely used and with good performance: tens to hundreds of Mbps. Its biggest change is that it's **all IP**. Even voice calls are carried as packets (Voice over LTE). That's chapter 1's switch from circuit switching to packet switching, finally reaching the phone network.

| Generation | Example | Big idea |
|---|---|---|
| 2G | GSM | Digital voice, TDMA, SIM cards |
| 3G | UMTS, CDMA2000 | Mobile data, CDMA |
| 4G | LTE | All IP, broadband speeds |
| 5G | 5G NR | Faster, lower latency, huge numbers of IoT devices |

Next, a check on cellular networks.
