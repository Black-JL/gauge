#!/usr/bin/env python3
"""
gaugebar.py — Gauge as a native macOS menu-bar app.

Shows live CPU in the menu bar; the dropdown breaks out CPU (overall + peak
core), memory, disk, and battery, and can open the full gauge dashboard.

Requires PyObjC (AppKit) — present in the python.org framework Python. It
reuses the pure-stdlib stat helpers from gauge.py, so no other dependencies.
"""

import os
import sys
import subprocess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gauge  # noqa: E402  (reuse _cpu_ticks/_cpu_percent/_mem_stats/…)

import objc  # noqa: E402
from Foundation import NSObject, NSTimer  # noqa: E402
from AppKit import (  # noqa: E402
    NSApplication, NSStatusBar, NSVariableStatusItemLength, NSMenu, NSMenuItem,
    NSApplicationActivationPolicyAccessory,
)


class GaugeBar(NSObject):
    def init(self):
        self = objc.super(GaugeBar, self).init()
        if self is None:
            return None
        self.prev = gauge._cpu_ticks()
        self.i = 0
        self.disk = gauge._disk_stats()
        self.batt = gauge._battery_stats()
        return self

    @objc.python_method
    def _row(self, menu, title):
        it = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, None, "")
        it.setEnabled_(False)
        menu.addItem_(it)
        return it

    def setup(self):
        bar = NSStatusBar.systemStatusBar()
        self.item = bar.statusItemWithLength_(NSVariableStatusItemLength)
        self.item.button().setTitle_("Gauge …")

        menu = NSMenu.alloc().init()
        self.mi_cpu = self._row(menu, "CPU  —")
        self.mi_mem = self._row(menu, "Memory  —")
        self.mi_disk = self._row(menu, "Disk  —")
        self.mi_batt = self._row(menu, "Battery  —")
        menu.addItem_(NSMenuItem.separatorItem())

        opn = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Open Dashboard", "openDash:", "")
        opn.setTarget_(self)
        menu.addItem_(opn)
        q = NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(
            "Quit Gauge", "quit:", "q")
        q.setTarget_(self)
        menu.addItem_(q)
        self.item.setMenu_(menu)

        self.timer = NSTimer.scheduledTimerWithTimeInterval_target_selector_userInfo_repeats_(
            1.0, self, "tick:", None, True)
        self.tick_(None)

    def tick_(self, timer):
        try:
            cur = gauge._cpu_ticks()
            pct = gauge._cpu_percent(self.prev, cur)
            self.prev = cur
            overall = sum(pct) / len(pct) if pct else 0.0
            peak = max(pct) if pct else 0.0
            mem = gauge._mem_stats()
            if self.i % 5 == 0:
                self.disk = gauge._disk_stats()
                self.batt = gauge._battery_stats()
            self.i += 1

            self.item.button().setTitle_("CPU %d%%" % round(overall * 100))
            self.mi_cpu.setTitle_("CPU   %d%%      peak core %d%%"
                                  % (round(overall * 100), round(peak * 100)))
            self.mi_mem.setTitle_("Memory   %.1f GB used   (%d%% of %d)"
                                  % (mem["used_gb"], round(mem["used_frac"] * 100),
                                     round(mem["total_gb"])))
            self.mi_disk.setTitle_("Disk   %d GB free   (%d%%)"
                                   % (round(self.disk["free_gb"]),
                                      round(self.disk["free_frac"] * 100)))
            state = "charging" if self.batt["charging"] else "on battery"
            self.mi_batt.setTitle_("Battery   %d%%   (%s)"
                                   % (round(self.batt["charge"] * 100), state))
        except Exception:
            pass

    def openDash_(self, sender):
        app = "/Applications/Gauge.app"
        if os.path.isdir(app):
            subprocess.Popen(["open", app])
        else:
            here = os.path.dirname(os.path.abspath(__file__))
            subprocess.Popen(["/usr/bin/python3", os.path.join(here, "gauge.py")])

    def quit_(self, sender):
        NSApplication.sharedApplication().terminate_(self)


def main():
    app = NSApplication.sharedApplication()
    app.setActivationPolicy_(NSApplicationActivationPolicyAccessory)
    delegate = GaugeBar.alloc().init()
    delegate.setup()
    app.run()


if __name__ == "__main__":
    main()
