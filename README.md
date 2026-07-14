# Gauge

A minimal, beautiful macOS system monitor — CPU, memory, and disk shown as
vintage-instrument dials. Inspired by Porsche gauge clusters and classic
analog meters.

## The app

`gauge.py` is the **live app** — a self-contained macOS system monitor built
on the minimal design (`gauge_A_minimal.html`). No third-party dependencies:
per-core CPU is read from the mach kernel via `ctypes`, memory from `vm_stat`,
disk from `os`, battery from `pmset`. It serves a tiny local web UI and opens
it in a chrome-less window; the server auto-quits a few seconds after that
window closes.

### Run it

```sh
python3 gauge.py            # run directly, or…
./build_app.sh              # build Gauge.app, then double-click it in Finder
```

`build_app.sh` packages everything into `Gauge.app` (launcher + `gauge.py` +
icon) so it launches from Finder. `create_icon.py` regenerates `Gauge.icns`
(requires Pillow; the committed `.icns` means you usually don't need to).

## Design mockups

The `gauge_*_*.html` files are **self-contained design mockups** (no build step
— just open in a browser). Each animates with plausible demo data plus a few
real values so the look can be judged. Minimal (A) is the chosen direction and
is what the live app implements.

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

- [x] Wire the primary design to **live system data** (pure Python stdlib).
- [x] Package as a double-clickable `.app` that launches from Finder.
- [ ] Optional: install to `/Applications`, add a menu-bar entry, code-sign.
