# Gauge

A minimal, beautiful macOS system monitor — CPU, memory, and disk shown as
vintage-instrument dials. Inspired by Porsche gauge clusters and classic
analog meters.

This repo currently holds **design mockups** (self-contained HTML, no build
step — just open in a browser). Each animates with plausible demo data plus
a few real values so the look can be judged before wiring live system data.

## What each gauge shows

- **CPU** — a dual-reading tachometer: the long needle is overall load across
  all cores, while an inner ring + short red needle tracks the single hottest
  core (so a spike on one core is visible without the whole gauge jumping).
- **Memory** — memory pressure / used GB of 32 GB.
- **Disk** — free space remaining (redlines when low). A small real-battery
  indicator (charge level + charging bolt) lives inside this dial.

## Mockups

| File | Direction |
|------|-----------|
| `gauge_A_minimal.html` | **Primary.** Pure white on true black, thin bezels, modern-minimal (Braun/Nomos-clean). |
| `gauge_B_997.html` | Porsche 911 (997) instrument cluster — brushed chrome rings, guilloché faces, Futura numerals. |
| `gauge_C_chrono.html` | Porsche Design chronograph — one blacked-out watch dial with tri-compax sub-registers. |
| `gauge_D_retro_green.html` | Retro chrome bezels + phosphor-green glowing dials (vintage lab/oscilloscope). |
| `gauge_E_vu.html` | Warm-backlit analog VU meters with a red PEAK lamp. |

Target machine for the real values shown: **Apple M1 Pro, 10 cores (8P/2E),
32 GB RAM**.

## Roadmap

- [ ] Wire the primary design to **live system data** (pure Python stdlib:
  per-core CPU via mach `host_processor_info` through `ctypes`, memory via
  `vm_stat`, disk via `os`, battery via `pmset` — no pip dependencies).
- [ ] Package as a double-clickable `.app` that launches from Finder, matching
  the companion Speed_Test tool.
