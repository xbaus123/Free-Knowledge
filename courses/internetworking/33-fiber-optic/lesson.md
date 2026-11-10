# Fiber-Optic Cable

*Chapter 2 · Topologies and the Physical Layer.*

Copper cables carry electricity. **Fiber-optic** cable carries **light**: pulses sent through strands of glass or plastic thinner than a human hair. A pulse of light is a `1`, no light is a `0`.

## How light stays inside

```
   jacket   ════════════════════════════════════════
   cladding ────────────────────────────────────────
   core        ╲    ╱╲    ╱╲    ╱╲    ╱╲    ╱
                ╲  ╱  ╲  ╱  ╲  ╱  ╲  ╱  ╲  ╱      ──▶ light
                 ╲╱    ╲╱    ╲╱    ╲╱    ╲╱
   cladding ────────────────────────────────────────
   jacket   ════════════════════════════════════════
```

A fiber has a glass **core** surrounded by **cladding**, a layer of glass that bends light slightly less. When light inside the core hits the cladding at a shallow angle, it reflects back in instead of escaping. That's **total internal reflection**, and it keeps the **signal contained within** the core for kilometers. An **outer jacket** protects the delicate fibers.

## Why fiber wins

- **Fast, high-bandwidth transmission over long distances with minimal loss.** Fiber attenuates far less than copper, so segments run for kilometers instead of 100 meters.
- **Resistant to RFI, EMI, and crosstalk.** Light isn't affected by electrical noise, and light in one fiber doesn't leak into the next. You can run fiber right beside power lines and heavy machinery.
- Harder to tap: you can't pick up its signal from outside the cable the way you can with copper.

The downsides: fiber and its optics cost more, and the glass is fragile. It can't be bent sharply, and joining two fibers takes special tools.

## Single-mode and multimode

Fiber **supports multiple modes**, which are the paths light can take through the core:

| | Single-mode | Multimode |
|---|---|---|
| Core | Very thin | Wider |
| Light paths | One, straight down the middle | Many, bouncing at different angles |
| Distance | Tens of kilometers | Up to a few hundred meters |
| Light source | Laser | Usually LEDs or cheaper lasers |
| Typical use | ISPs, long links between buildings and cities | Inside a building or data center |

In multimode fiber, light taking different paths arrives at slightly different times and the pulses smear together, which limits the distance. Single-mode fiber has only one path, so it doesn't have this problem.

## Discussion: Comcast vs Fios

Two big US home Internet services make a good comparison:

- **Comcast (Xfinity)** uses a **hybrid fiber-coax** network: fiber runs from the provider out to the neighborhood, then **broadband coax** covers the last stretch to your home. Your coax line is shared with the neighbors, so speeds can drop at busy times, and upload speeds are usually much lower than download.
- **Verizon Fios** runs **fiber all the way to the home** ("fiber to the premises"). There's no coax in the path, so it can offer upload speeds as fast as download.

Both are "broadband Internet". The difference is what the last stretch to your home is made of.

Next, a check on fiber.
