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

### Two forms

- **`Gauge.app`** — the windowed dashboard (three dials in a chrome-less
  window). Pure stdlib; runs on the system `/usr/bin/python3`.
- **`GaugeBar.app`** — a native **menu-bar** app (`NSStatusBar`). The menu bar
  shows live CPU; the dropdown breaks out CPU (overall + peak core), memory,
  disk, and battery, plus **Open Dashboard** and **Quit**. Requires PyObjC
  (`import AppKit`) — bundled with the python.org framework Python; if missing,
  `pip3 install pyobjc`.

### Install / run

```sh
./install.sh               # build both apps and copy them to /Applications
python3 gauge.py           # or just run the dashboard directly
```

`build_app.sh` / `build_bar.sh` package each `.app` (launcher + scripts + icon)
for Finder. `create_icon.py` regenerates `Gauge.icns` (needs Pillow; the
committed `.icns` means you usually don't need to).

**Menu-bar difference for a Safari build:** the dashboard opens its UI in
Chrome's app mode (a chrome-less window). Safari has no chrome-less mode from
the CLI, so a Safari build would show the UI in a normal Safari window with the
full address bar/toolbar — functional, but it reads as a web page, not an app.
A truly native window would use a WebView (PyObjC), trading the zero-Chrome
requirement for the PyObjC dependency.

## Desktop widget (Übersicht)

`ubersicht/gauge.widget/` is a live desktop widget — the same dials, pinned to
your desktop, updating every second with CSS-eased needles. It adds a live
**network throughput** row (↓/↑ current rate, read from interface byte-counter
deltas — this is *current activity*, not a speed test).

```sh
brew install --cask ubersicht     # one-time, if not already installed
./install_widget.sh               # copies the widget in and launches Übersicht
```

The widget's `gauge_stats.py` is a self-contained one-shot JSON emitter (same
stdlib approach as the app). Drag the widget to reposition; Übersicht remembers.

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
- [x] Install to `/Applications`; add a native menu-bar app (`GaugeBar.app`).
- [ ] Optional: code-sign / notarize; launch-at-login; menu-bar mini-graphs.
