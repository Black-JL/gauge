#!/usr/bin/env python3
"""One-shot system stats as JSON, for the Übersicht Gauge widget.

Self-contained (no third-party deps): per-core CPU from the mach kernel via
ctypes, memory from vm_stat, disk from os, battery from pmset.
"""
import ctypes
import ctypes.util
import json
import re
import shutil
import subprocess
import time

_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
_natural_t = ctypes.c_uint
_integer_t = ctypes.c_int
_libc.mach_host_self.restype = ctypes.c_uint
_libc.mach_task_self.restype = ctypes.c_uint
_libc.host_processor_info.restype = ctypes.c_int
_libc.host_processor_info.argtypes = [
    ctypes.c_uint, ctypes.c_int, ctypes.POINTER(_natural_t),
    ctypes.POINTER(ctypes.POINTER(_integer_t)), ctypes.POINTER(_natural_t)]
_libc.vm_deallocate.argtypes = [ctypes.c_uint, ctypes.c_void_p, ctypes.c_size_t]


def _ticks():
    host = _libc.mach_host_self()
    ncpu = _natural_t(0)
    info = ctypes.POINTER(_integer_t)()
    cnt = _natural_t(0)
    if _libc.host_processor_info(host, 2, ctypes.byref(ncpu),
                                 ctypes.byref(info), ctypes.byref(cnt)) != 0:
        raise OSError("host_processor_info failed")
    n = ncpu.value
    t = [[info[i * 4 + s] for s in range(4)] for i in range(n)]
    _libc.vm_deallocate(_libc.mach_task_self(), ctypes.cast(info, ctypes.c_void_p),
                        cnt.value * ctypes.sizeof(_integer_t))
    return t


def cpu():
    a = _ticks()
    time.sleep(0.25)
    b = _ticks()
    pct = []
    for i in range(min(len(a), len(b))):
        du = b[i][0] - a[i][0]; ds = b[i][1] - a[i][1]
        di = b[i][2] - a[i][2]; dn = b[i][3] - a[i][3]
        busy = du + ds + dn; total = busy + di
        pct.append(busy / total if total else 0.0)
    return {"overall": sum(pct) / len(pct) if pct else 0.0,
            "peak": max(pct) if pct else 0.0, "cores": len(pct)}


def mem():
    total = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]))
    out = subprocess.check_output(["vm_stat"]).decode()
    m = re.search(r"page size of (\d+) bytes", out)
    ps = int(m.group(1)) if m else 4096

    def pg(name):
        mm = re.search(name + r":\s+(\d+)\.", out)
        return int(mm.group(1)) if mm else 0
    used = (pg(r"Pages active") + pg(r"Pages wired down")
            + pg(r"Pages occupied by compressor")) * ps
    gib = 1024 ** 3
    return {"used_frac": used / total if total else 0.0,
            "used_gb": used / gib, "total_gb": total / gib}


def disk():
    for p in ("/System/Volumes/Data", "/"):
        try:
            u = shutil.disk_usage(p)
            gb = 1_000_000_000
            return {"free_frac": u.free / u.total if u.total else 0.0,
                    "free_gb": u.free / gb, "total_gb": u.total / gb}
        except Exception:
            continue
    return {"free_frac": 0.0, "free_gb": 0, "total_gb": 0}


def battery():
    try:
        out = subprocess.check_output(["pmset", "-g", "batt"]).decode()
    except Exception:
        return {"present": False, "charge": 1.0, "charging": True}
    m = re.search(r"(\d+)%", out)
    return {"present": "InternalBattery" in out,
            "charge": int(m.group(1)) / 100 if m else 1.0,
            "charging": ("AC Power" in out) or ("charging" in out) or ("charged" in out)}


_NET_STATE = "/tmp/gauge_net_state.json"


def _net_counters():
    """Sum received/sent bytes across physical interfaces (skip loopback)."""
    out = subprocess.check_output(["netstat", "-ib"]).decode().splitlines()
    seen = {}
    ib = ob = 0
    for line in out[1:]:
        f = line.split()
        if len(f) < 11 or f[0].startswith("lo") or f[0] in seen:
            continue
        try:
            ib += int(f[6]); ob += int(f[9])
        except ValueError:
            continue
        seen[f[0]] = 1
    return ib, ob


def net():
    """Current throughput in bytes/sec, from the delta since the last call."""
    ib, ob = _net_counters()
    now = time.time()
    prev = None
    try:
        with open(_NET_STATE) as f:
            prev = json.load(f)
    except Exception:
        pass
    down = up = 0.0
    if prev:
        dt = now - prev["t"]
        if 0 < dt < 30:
            down = max(0.0, (ib - prev["ib"]) / dt)
            up = max(0.0, (ob - prev["ob"]) / dt)
    try:
        with open(_NET_STATE, "w") as f:
            json.dump({"t": now, "ib": ib, "ob": ob}, f)
    except Exception:
        pass
    return {"down_bps": down, "up_bps": up}


if __name__ == "__main__":
    print(json.dumps({"cpu": cpu(), "mem": mem(), "disk": disk(),
                      "battery": battery(), "net": net()}))
