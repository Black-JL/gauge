# PROJECT LOG — Gauge

A running record of what was built and why. Newest at the bottom within a day.
See `PLAN.md` for the concept and `README.md` for usage.

## 2026-07-14 — build day (whole project)

Order roughly matches the git history (`git log --oneline`).

1. **Design mockups (5 directions).** Self-contained HTML mockups A–E so the
   look could be judged side by side. Minimal (A) chosen; 997 (B), chronograph
   (C), and VU (E) later reused; retro-green (D) shelved.
2. **CPU dual-reading.** Fixed "one core jumps, the whole gauge jerks" by adding
   an inner needle for the hottest core alongside the overall-load needle.
3. **Battery fix.** Early builds read the disk-as-battery glyph as the *real*
   battery and showed it near-empty while plugged in. Resolved: disk shows %
   free; a genuine battery indicator (from `pmset`) lives inside the disk dial.
4. **Removed busy core-pip lights** on the middle dial — they read as divorced
   from the data. The dual needle tells the story instead.
5. **Live app (`gauge.py`).** Wired the minimal design to real data using pure
   Python stdlib (mach `ctypes` per-core CPU, `vm_stat`, `pmset`, `os`). Serves
   a local web UI in a chrome-less Chrome window; auto-quits when closed.
6. **`Gauge.app`** — Finder-launchable bundle + `Gauge.icns` (`create_icon.py`).
7. **`GaugeBar.app`** — native menu-bar app via PyObjC `NSStatusBar`. Fixed a
   `BadPrototypeError` by decorating the multi-arg helper `@objc.python_method`.
8. **Übersicht desktop widget** — live desktop dials + a network-throughput row.
   Then simplified: readings inset into each dial, network row dropped. Later the
   widget was **turned off** entirely (user doesn't want it on the main screen);
   source kept in `ubersicht/`.
9. **Always-on LAN server (`gauge_server.py`)** for an old iPad mini — persistent,
   binds `0.0.0.0:8770`, installed as a LaunchAgent. Made the page old-iOS-safe
   (XHR, SVG-attribute needle transforms; works back to iOS 10).
10. **Switched the iPad display to VU meters** with the dual-needle CPU + PEAK
    lamp + battery-on-disk.
11. **Needle ballistics.** Added rAF easing; then differentiated by style —
    VU slow/fluid (ease ~0.035), car-style gauges snappy (~0.22/0.42). Also moved
    to compact fixed sizing (the user preferred the earlier smaller mockups).
12. **Chronograph cleanup.** Removed the 20/80 main-scale numerals that the
    subdials were sitting on top of.
13. **Watch + Clock pair (`gauge_pair.html`).** Added a matching real-time clock
    beside the system chronograph: inner tick ring, real hour/min/sec hands, and
    real DATE and DAY subdials (were meaningless placeholders before).
14. **Chooser launcher.** Rewrote `gauge_server.py` to route a chooser at `/`
    plus four live views (`/minimal`, `/vintage`, `/vu`, `/pair`), `/core.js`,
    and `/stats`. Built the shared render engine `web/core.js` and thin themed
    shells in `web/`. `Gauge.app` now boots the server if needed and opens the
    chooser in a chrome-less Chrome window.

### Verified this session
- All routes return 200; unknown paths 404; `/stats` serves live JSON.
- Chooser, VU, and Watch+Clock views render live with no console errors.
- Clock shows correct real time/date (Tue 14 Jul); DATE "14", DAY "TUE".
- LaunchAgent restarted; serves the new routing on `:8770`.
- `Gauge.app` rebuilt + reinstalled to `/Applications` (now self-contained:
  bundles `gauge_server.py` + `web/`).
- Everything committed and pushed to `github.com/Black-JL/gauge`.

## 2026-07-15 — documentation
- Added `PLAN.md` (concept + tools tried) and this `PROJECT_LOG.md`.
- Updated `README.md` to describe the chooser launcher and the four-view server.
