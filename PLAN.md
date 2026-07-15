# PLAN — Gauge

## The idea (in one line)
A beautiful macOS system monitor that shows **CPU, memory, disk, and battery** as
**vintage-instrument dials** — Porsche gauge clusters and classic analog meters,
not bar charts.

## Core requirements (what the user asked for)
- Vintage-Porsche aesthetic: white foreground on true black; gauges sweep
  0 → "rev limiter" with a red zone near the top.
- **CPU** like a tachometer, with a **dual reading**: outer/long needle = overall
  load across all cores, inner/short needle = the single hottest (jumping) core —
  so one spiking core is visible without the whole gauge jerking.
- **Memory** = pressure / used GB.
- **Disk** = free space (like a fuel gauge), with a small **real battery**
  indicator living *inside* the disk dial (charge + charging bolt).
- Three dials read better than four.
- **Chooser on launch**: pick 1 of 4 displays — Vintage (997), Clean (minimal),
  Watch+Clock (chronograph + real clock), VU meters.
- **Always-on display** for an old iPad mini over the LAN.
- Needle feel: VU meters = slow / heavy / fluid; car-style round gauges = snappy.

## Design directions explored (mockups)
| File | Direction | Verdict |
|------|-----------|---------|
| `gauge_A_minimal.html` | Pure white-on-black, thin bezels (Braun/Nomos) | **Chosen primary** |
| `gauge_B_997.html` | Porsche 997 cluster, chrome rings, guilloché | Kept as "Vintage" |
| `gauge_C_chrono.html` | Porsche Design chronograph watch | Became the Watch+Clock pair |
| `gauge_D_retro_green.html` | Chrome + phosphor-green glow | Not pursued |
| `gauge_E_vu.html` | Warm analog VU meters + PEAK lamp | Chosen for the iPad display |

## Tools / techniques used
- **Stats (pure Python stdlib, no deps):** per-core CPU via mach
  `host_processor_info` through `ctypes`; memory via `vm_stat` + `sysctl`;
  disk via `shutil.disk_usage`; battery via `pmset -g batt`; network via
  `netstat -ib` deltas.
- **Serving:** stdlib `http.server.ThreadingHTTPServer`, a background sampler
  thread, JSON `/stats` endpoint. `web/core.js` is one shared SVG render engine;
  thin per-view shells set `window.GV` and load it.
- **Gauges:** SVG needles rotated via `transform="rotate(a cx cy)"`, 270° sweep
  (`angle = 135 + f*270`), gap at the bottom.
- **Needle ballistics:** requestAnimationFrame easing — car gauges fast
  (~0.22/0.42), VU slow (ease ~0.035, peak attack 0.30 / release 0.035).
- **Packaging:** macOS `.app` bundles (Info.plist, `LSUIElement`, launcher shell);
  system `/usr/bin/python3` for stdlib paths, python.org Python for PyObjC.
- **Menu-bar app:** PyObjC / AppKit `NSStatusBar` (`gaugebar.py`).
- **Always-on:** LaunchAgent (RunAtLoad / KeepAlive) running `gauge_server.py`;
  Chrome app-mode (`--app=URL`) for chrome-less windows.
- **Old-iOS compatibility:** XHR (not fetch), SVG-attribute (not CSS) transforms —
  works back to iOS 10 / iPad mini 2.
- **Tried then dropped:** an Übersicht desktop widget (source kept in
  `ubersicht/`, but turned off — the user doesn't want it on the main screen);
  a live network-throughput ticker (removed from the widget UI).

## Current state
`Gauge.app` opens the chooser → four live views, all fed by `/stats`, served by
`gauge_server.py` (also running as a LaunchAgent on port 8770 for the iPad).
Menu-bar `GaugeBar.app` shows live CPU. All pushed to `github.com/Black-JL/gauge`.

## Open / optional next steps
- Visually eyeball the **minimal** and **vintage** live routes (VU + pair were
  screenshot-verified; those two were built in `core.js` but not re-checked).
- Tune `Gauge.app` Chrome window size (currently `560x500` in `build_app.sh`).
- Optional: code-sign / notarize, launch-at-login, menu-bar mini-graphs.
