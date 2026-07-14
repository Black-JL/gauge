#!/usr/bin/env python3
"""
gauge.py — a minimal live macOS system monitor.

CPU (per-core), memory, disk, and battery shown as vintage-instrument dials.
No third-party dependencies: per-core CPU is read straight from the mach
kernel via ctypes, memory from vm_stat, disk from os, battery from pmset.

It serves a tiny local web UI and opens it in a chrome-less app window.
The server auto-quits a few seconds after that window closes.

Usage:  python3 gauge.py
"""

import ctypes
import ctypes.util
import json
import os
import re
import shutil
import subprocess
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ── CPU: per-core load via mach host_processor_info ──────────────────────────

_libc = ctypes.CDLL(ctypes.util.find_library("c"), use_errno=True)
_PROCESSOR_CPU_LOAD_INFO = 2
_CPU_STATE_MAX = 4          # user, system, idle, nice
_natural_t = ctypes.c_uint
_integer_t = ctypes.c_int

_libc.mach_host_self.restype = ctypes.c_uint
_libc.mach_task_self.restype = ctypes.c_uint
_libc.host_processor_info.restype = ctypes.c_int
_libc.host_processor_info.argtypes = [
    ctypes.c_uint, ctypes.c_int,
    ctypes.POINTER(_natural_t),
    ctypes.POINTER(ctypes.POINTER(_integer_t)),
    ctypes.POINTER(_natural_t),
]
_libc.vm_deallocate.argtypes = [ctypes.c_uint, ctypes.c_void_p, ctypes.c_size_t]


def _cpu_ticks():
    """Return a list of [user, system, idle, nice] tick counts per core."""
    host = _libc.mach_host_self()
    ncpu = _natural_t(0)
    info = ctypes.POINTER(_integer_t)()
    cnt = _natural_t(0)
    kr = _libc.host_processor_info(
        host, _PROCESSOR_CPU_LOAD_INFO,
        ctypes.byref(ncpu), ctypes.byref(info), ctypes.byref(cnt))
    if kr != 0:
        raise OSError("host_processor_info failed: %d" % kr)
    n = ncpu.value
    ticks = [[info[i * _CPU_STATE_MAX + s] for s in range(_CPU_STATE_MAX)]
             for i in range(n)]
    _libc.vm_deallocate(_libc.mach_task_self(),
                        ctypes.cast(info, ctypes.c_void_p),
                        cnt.value * ctypes.sizeof(_integer_t))
    return ticks


def _cpu_percent(prev, cur):
    """Per-core busy fraction (0..1) from two tick samples."""
    out = []
    for i in range(min(len(prev), len(cur))):
        du = cur[i][0] - prev[i][0]
        ds = cur[i][1] - prev[i][1]
        di = cur[i][2] - prev[i][2]
        dn = cur[i][3] - prev[i][3]
        busy = du + ds + dn
        total = busy + di
        out.append(busy / total if total > 0 else 0.0)
    return out


# ── Memory via vm_stat + sysctl ──────────────────────────────────────────────

def _mem_stats():
    total = int(subprocess.check_output(["sysctl", "-n", "hw.memsize"]))
    out = subprocess.check_output(["vm_stat"]).decode()
    m = re.search(r"page size of (\d+) bytes", out)
    ps = int(m.group(1)) if m else 4096

    def pages(name):
        mm = re.search(name + r":\s+(\d+)\.", out)
        return int(mm.group(1)) if mm else 0

    active = pages(r"Pages active")
    wired = pages(r"Pages wired down")
    comp = pages(r"Pages occupied by compressor")
    used = (active + wired + comp) * ps
    gib = 1024 ** 3
    return {
        "used_frac": used / total if total else 0.0,
        "used_gb": used / gib,
        "total_gb": total / gib,
    }


# ── Disk via os/shutil ───────────────────────────────────────────────────────

def _disk_stats():
    for path in ("/System/Volumes/Data", "/"):
        try:
            u = shutil.disk_usage(path)
            gb = 1_000_000_000  # decimal GB, matches Finder / df -H
            return {
                "free_frac": u.free / u.total if u.total else 0.0,
                "free_gb": u.free / gb,
                "total_gb": u.total / gb,
            }
        except Exception:
            continue
    return {"free_frac": 0.0, "free_gb": 0, "total_gb": 0}


# ── Battery via pmset ────────────────────────────────────────────────────────

def _battery_stats():
    try:
        out = subprocess.check_output(["pmset", "-g", "batt"]).decode()
    except Exception:
        return {"present": False, "charge": 1.0, "charging": True}
    present = "InternalBattery" in out
    m = re.search(r"(\d+)%", out)
    charge = int(m.group(1)) / 100 if m else 1.0
    charging = ("AC Power" in out) or ("charging" in out) or ("charged" in out)
    return {"present": present, "charge": charge, "charging": charging}


# ── System info ──────────────────────────────────────────────────────────────

def _sys_info(ncores):
    try:
        chip = subprocess.check_output(
            ["sysctl", "-n", "machdep.cpu.brand_string"]).decode().strip()
    except Exception:
        chip = "CPU"
    return {"chip": chip, "cores": ncores}


# ── Background sampler ───────────────────────────────────────────────────────

STATS = {"cpu": {"overall": 0.0, "peak": 0.0},
         "mem": {"used_frac": 0.0, "used_gb": 0, "total_gb": 0},
         "disk": {"free_frac": 0.0, "free_gb": 0, "total_gb": 0},
         "battery": {"present": True, "charge": 1.0, "charging": True},
         "sys": {"chip": "CPU", "cores": 0}}
_lock = threading.Lock()


def _sampler():
    prev = _cpu_ticks()
    ncores = len(prev)
    sysinfo = _sys_info(ncores)
    time.sleep(0.5)
    i = 0
    while True:
        try:
            cur = _cpu_ticks()
            pct = _cpu_percent(prev, cur)
            prev = cur
            overall = sum(pct) / len(pct) if pct else 0.0
            peak = max(pct) if pct else 0.0

            mem = _mem_stats()
            disk = STATS["disk"] if i % 8 else _disk_stats()      # ~4 s
            batt = STATS["battery"] if i % 10 else _battery_stats()  # ~5 s

            with _lock:
                STATS["cpu"] = {"overall": overall, "peak": peak}
                STATS["mem"] = mem
                STATS["disk"] = disk
                STATS["battery"] = batt
                STATS["sys"] = sysinfo
        except Exception:
            pass
        i += 1
        time.sleep(0.5)


# ── HTTP server ──────────────────────────────────────────────────────────────

_last_ping = [0.0]
_pinged = [False]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/stats"):
            _last_ping[0] = time.time()
            _pinged[0] = True
            with _lock:
                body = json.dumps(STATS).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)


def _watchdog():
    """Quit shortly after the UI window closes (no /stats pings)."""
    while True:
        time.sleep(2)
        if _pinged[0] and (time.time() - _last_ping[0]) > 6:
            os._exit(0)


def _open_window(url):
    chrome = "/Applications/Google Chrome.app"
    if os.path.isdir(chrome):
        subprocess.Popen(["open", "-na", "Google Chrome", "--args",
                          "--app=" + url, "--window-size=1180,560"])
    else:
        webbrowser.open(url)


def main():
    threading.Thread(target=_sampler, daemon=True).start()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    url = "http://127.0.0.1:%d/" % port
    threading.Thread(target=_watchdog, daemon=True).start()
    # small delay so the first sample is ready before the page loads
    time.sleep(0.6)
    _open_window(url)
    server.serve_forever()


# ── Embedded UI (minimal design) ─────────────────────────────────────────────

HTML = r"""<!doctype html><html><head><meta charset="utf-8"><title>Gauge</title>
<style>
  :root{--ink:#ffffff; --dim:#565656; --dim2:#8c8c8c; --red:#ff3b30; --green:#32d74b;}
  html,body{height:100%;margin:0;}
  body{background:#000;color:var(--ink);
    font-family:'Helvetica Neue','Inter',system-ui,sans-serif;font-weight:300;
    display:flex;flex-direction:column;align-items:center;justify-content:center;
    -webkit-font-smoothing:antialiased;user-select:none;overflow:hidden;}
  .brand{letter-spacing:.62em;font-size:12px;color:var(--dim2);text-transform:uppercase;
    margin-bottom:34px;padding-left:.62em;font-weight:400;}
  .cluster{display:flex;align-items:center;justify-content:center;gap:30px;}
  .gauge{display:flex;flex-direction:column;align-items:center;}
  .gauge.side .dial{width:236px;height:236px;}
  .gauge.center .dial{width:344px;height:344px;}
  .gauge.side{transform:translateY(30px);}
  .dial{position:relative;filter:drop-shadow(0 10px 26px rgba(0,0,0,.7));}
  svg{display:block;width:100%;height:100%;}
  .readout{margin-top:20px;text-align:center;}
  .val{font-size:25px;font-weight:200;letter-spacing:.04em;color:var(--ink);font-variant-numeric:tabular-nums;}
  .center .val{font-size:33px;}
  .val .u{font-size:.46em;color:var(--dim2);font-weight:300;letter-spacing:.15em;margin-left:.25em;}
  .sub{font-size:10.5px;letter-spacing:.26em;color:var(--dim);text-transform:uppercase;margin-top:7px;}
  .footer{margin-top:44px;display:flex;gap:44px;align-items:center;
    font-size:10.5px;letter-spacing:.28em;color:var(--dim);text-transform:uppercase;}
  .footer b{color:var(--dim2);font-weight:400;}
</style></head><body>
<div class="brand">Gauge</div>
<div class="cluster">
  <div class="gauge side" id="gauge-mem"><div class="dial"></div>
    <div class="readout"><div class="val">--</div><div class="sub">Memory</div></div></div>
  <div class="gauge center" id="gauge-cpu"><div class="dial"></div>
    <div class="readout"><div class="val">--</div><div class="sub">CPU</div></div></div>
  <div class="gauge side" id="gauge-disk"><div class="dial"></div>
    <div class="readout"><div class="val">--</div><div class="sub">Disk</div></div></div>
</div>
<div class="footer">
  <span id="f-chip">--</span><span><b id="f-cores">--</b> Cores</span>
  <span><b id="f-ram">--</b> GB</span><span id="clock">--</span>
</div>
<script>
const CX=150,CY=150,START=135,SWEEP=270;
const d2r=d=>d*Math.PI/180;
const polar=(r,d)=>[CX+r*Math.cos(d2r(d)),CY+r*Math.sin(d2r(d))];
const angleFor=f=>START+f*SWEEP;
function arcPath(r,f0,f1){const a0=angleFor(f0),a1=angleFor(f1),[x0,y0]=polar(r,a0),[x1,y1]=polar(r,a1);
  return 'M '+x0+' '+y0+' A '+r+' '+r+' 0 '+((a1-a0)>180?1:0)+' 1 '+x1+' '+y1;}

function buildDial(cfg){
  let ticks='',nums='';
  const minors=cfg.minorCount||0;
  for(let i=0;i<=minors;i++){const f=i/minors,a=angleFor(f),p0=polar(122,a),p1=polar(116,a);
    ticks+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="#3a3a3a" stroke-width="1"/>';}
  cfg.majors.forEach(function(m){const a=angleFor(m.f),inRed=cfg.redBand&&m.f>=cfg.redBand[0]-1e-6&&m.f<=cfg.redBand[1]+1e-6;
    const col=inRed?'var(--red)':'var(--ink)';const p0=polar(123,a),p1=polar(107,a),tp=polar(90,a);
    ticks+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="'+col+'" stroke-width="1.6" stroke-linecap="round"/>';
    nums+='<text x="'+tp[0]+'" y="'+(tp[1]+5)+'" text-anchor="middle" font-size="15" font-weight="300" fill="'+col+'" letter-spacing="0.5">'+m.label+'</text>';});
  let batt='';
  if(cfg.battery)batt='<g class="battind" transform="translate(150 176)">'
    +'<text x="0" y="-11" text-anchor="middle" font-size="7" letter-spacing="1.8" fill="var(--dim2)">BATTERY</text>'
    +'<rect x="-14" y="-6.5" width="26" height="13" rx="2.5" fill="none" stroke="var(--dim2)" stroke-width="1.2"/>'
    +'<rect x="12" y="-3" width="2.6" height="6" rx="1" fill="var(--dim2)"/>'
    +'<rect class="battfill" x="-11.5" y="-4" width="21" height="8" rx="1" fill="var(--green)"/>'
    +'<path class="battbolt" d="M 1.5 -5 L -3 0.5 L 0 0.5 L -1.5 5 L 3.5 -1 L 0.5 -1 Z" fill="#04270f"/>'
    +'<text class="battpct" x="0" y="19" text-anchor="middle" font-size="8" fill="var(--dim2)" font-variant-numeric="tabular-nums">--</text></g>';
  let innerTrack='',innerNeedle='';
  if(cfg.inner){
    innerTrack='<path d="'+arcPath(76,0,1)+'" stroke="#191919" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
      +'<path class="innerfill" d="'+arcPath(76,0,0.002)+'" stroke="var(--ink)" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
      +'<text x="150" y="176" text-anchor="middle" font-size="7.5" letter-spacing="2" fill="var(--dim)">PEAK CORE</text>';
    innerNeedle='<g class="needle2" transform="rotate('+angleFor(0)+' 150 150)"><polygon points="216,150 150,149.1 150,150.9" fill="var(--red)"/></g>';
  }
  const red=cfg.redBand?'<path d="'+arcPath(124,cfg.redBand[0],cfg.redBand[1])+'" stroke="var(--red)" stroke-width="4" fill="none"/>':'';
  return '<svg viewBox="0 0 300 300"><defs>'
    +'<radialGradient id="face'+cfg.faceName+'" cx="50%" cy="42%" r="72%">'
    +'<stop offset="0%" stop-color="#0e0e0e"/><stop offset="70%" stop-color="#070707"/><stop offset="100%" stop-color="#000"/></radialGradient>'
    +'<filter id="nd'+cfg.faceName+'" x="-40%" y="-40%" width="180%" height="180%">'
    +'<feDropShadow dx="0" dy="1" stdDeviation="1.4" flood-color="#000" flood-opacity="0.6"/></filter></defs>'
    +'<circle cx="150" cy="150" r="147" fill="none" stroke="#2a2a2a" stroke-width="1"/>'
    +'<circle cx="150" cy="150" r="143" fill="none" stroke="#161616" stroke-width="1.5"/>'
    +'<circle cx="150" cy="150" r="140" fill="url(#face'+cfg.faceName+')"/>'
    +red+ticks+nums+batt+innerTrack
    +'<text x="150" y="120" text-anchor="middle" font-size="11" letter-spacing="4" fill="var(--dim2)" font-weight="400">'+cfg.faceName+'</text>'
    +'<text x="150" y="210" text-anchor="middle" font-size="8.5" letter-spacing="2.5" fill="var(--dim)" font-weight="400">'+(cfg.faceUnit||'')+'</text>'
    +innerNeedle
    +'<g class="needle" filter="url(#nd'+cfg.faceName+')" transform="rotate('+angleFor(0)+' 150 150)">'
    +'<polygon points="150,150 124,148.8 124,151.2" fill="#3a3a3a"/>'
    +'<polygon points="256,150 166,149 166,151" fill="var(--ink)"/>'
    +'<polygon points="256,150 238,149.7 238,150.3" fill="var(--red)"/></g>'
    +'<circle cx="150" cy="150" r="6.5" fill="#e8e8e8"/><circle cx="150" cy="150" r="2.4" fill="#000"/></svg>';
}

const CPU={el:'#gauge-cpu',cfg:{faceName:'CPU',faceUnit:'× 10 %  OVERALL',redBand:[0.85,1],minorCount:50,inner:true,
  majors:[0,1,2,3,4,5,6,7,8,9,10].map(n=>({f:n/10,label:String(n)}))}};
const MEM={el:'#gauge-mem',cfg:{faceName:'MEM',faceUnit:'% USED',redBand:[0.85,1],minorCount:50,
  majors:[0,20,40,60,80,100].map(n=>({f:n/100,label:String(n)}))}};
const DISK={el:'#gauge-disk',cfg:{faceName:'DISK',faceUnit:'% FREE',redBand:[0,0.15],minorCount:40,battery:true,
  majors:[{f:0,label:'0'},{f:0.5,label:'50'},{f:1,label:'100'}]}};

function mount(g){const host=document.querySelector(g.el+' .dial');host.innerHTML=buildDial(g.cfg);
  g.needle=host.querySelector('.needle');g.needle2=host.querySelector('.needle2');g.innerfill=host.querySelector('.innerfill');
  g.battfill=host.querySelector('.battfill');g.battbolt=host.querySelector('.battbolt');g.battpct=host.querySelector('.battpct');
  g.valEl=document.querySelector(g.el+' .val');g.subEl=document.querySelector(g.el+' .sub');g.cur=0;g.peak=0;}
[MEM,CPU,DISK].forEach(mount);
const setN=(g,f)=>g.needle.setAttribute('transform','rotate('+angleFor(Math.max(0,Math.min(1,f)))+' 150 150)');

let tgt={overall:0,peak:0,mem:0,disk:0.5};
let tot={memTotal:0,diskTotal:0,cores:0,chip:''};
let battery={present:true,charge:1.0,charging:true};

async function poll(){
  try{
    const r=await fetch('/stats',{cache:'no-store'});
    const s=await r.json();
    tgt.overall=s.cpu.overall; tgt.peak=s.cpu.peak;
    tgt.mem=s.mem.used_frac; tgt.disk=s.disk.free_frac;
    tot.memTotal=s.mem.total_gb; tot.diskTotal=s.disk.total_gb;
    tot.cores=s.sys.cores; tot.chip=s.sys.chip;
    battery=s.battery;
    document.getElementById('f-chip').textContent=s.sys.chip;
    document.getElementById('f-cores').textContent=s.sys.cores;
    document.getElementById('f-ram').textContent=Math.round(s.mem.total_gb);
  }catch(e){}
}
poll(); setInterval(poll,1000);

function animate(){
  CPU.cur+=(tgt.overall-CPU.cur)*0.12; CPU.peak+=(tgt.peak-CPU.peak)*0.30;
  MEM.cur+=(tgt.mem-MEM.cur)*0.12; DISK.cur+=(tgt.disk-DISK.cur)*0.12;
  setN(MEM,MEM.cur);setN(CPU,CPU.cur);setN(DISK,DISK.cur);
  CPU.needle2.setAttribute('transform','rotate('+angleFor(Math.min(1,CPU.peak))+' 150 150)');
  CPU.innerfill.setAttribute('d',arcPath(76,0,Math.max(0.002,Math.min(1,CPU.peak))));
  CPU.innerfill.setAttribute('stroke',CPU.peak>0.85?'var(--red)':'var(--ink)');

  const bc=battery.charge,low=bc<0.15;
  DISK.battfill.setAttribute('width',(21*Math.max(0,Math.min(1,bc))).toFixed(1));
  DISK.battfill.setAttribute('fill',low?'var(--red)':'var(--green)');
  DISK.battbolt.setAttribute('opacity',battery.charging?1:0);
  DISK.battpct.textContent=Math.round(bc*100)+'%';

  CPU.valEl.innerHTML=Math.round(CPU.cur*100)+'<span class="u">%</span>';
  CPU.subEl.textContent='peak '+Math.round(CPU.peak*100)+'%';
  MEM.valEl.innerHTML=(MEM.cur*tot.memTotal).toFixed(1)+'<span class="u">GB</span>';
  MEM.subEl.textContent=Math.round(MEM.cur*100)+'% of '+Math.round(tot.memTotal);
  DISK.valEl.innerHTML=Math.round(DISK.cur*100)+'<span class="u">%</span>';
  DISK.subEl.textContent=Math.round(DISK.cur*tot.diskTotal)+' GB free';
  DISK.valEl.style.color=DISK.cur<0.12?'var(--red)':'var(--ink)';
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
function clk(){const n=new Date();document.getElementById('clock').textContent=n.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit'});}
clk();setInterval(clk,10000);
</script></body></html>"""


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
