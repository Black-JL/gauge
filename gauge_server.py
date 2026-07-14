#!/usr/bin/env python3
"""
gauge_server.py — always-on LAN display server for the Gauge VU meters.

Serves a full-screen VU-meter dashboard over the local network so an old iPad /
iPhone / any browser can be left on as a dedicated display.

Binds 0.0.0.0 on a fixed port, never auto-quits, and uses a compatibility-
friendly page (XHR, SVG-attribute needles). Reuses gauge.py's stdlib sampler.

Usage:  python3 gauge_server.py         (port 8770, or set GAUGE_PORT)
Then on the iPad:  http://<this-mac-ip>:8770/
"""

import json
import os
import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import gauge  # reuse _sampler / STATS / _lock and the stat helpers

PORT = int(os.environ.get("GAUGE_PORT", "8770"))


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/stats"):
            with gauge._lock:
                body = json.dumps(gauge.STATS).encode()
            ctype = "application/json"
        else:
            body = DISPLAY_HTML.encode()
            ctype = "text/html; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass


def lan_ips():
    ips = []
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.append(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    try:
        host = socket.gethostname()
        if not host.endswith(".local"):
            host += ".local"
        ips.append(host)
    except Exception:
        pass
    return ips


def main():
    threading.Thread(target=gauge._sampler, daemon=True).start()
    time.sleep(0.6)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print("Gauge display server running. Open on any device on your network:")
    for ip in lan_ips():
        print("    http://%s:%d/" % (ip, PORT))
    server.serve_forever()


DISPLAY_HTML = r"""<!doctype html><html><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<title>Gauge</title>
<style>
  :root{--face:#f0e5c6;--scale:#1c1710;--dim:#7a6c48;--red:#c0261b;--glow:#ffb552;}
  *{margin:0;padding:0;box-sizing:border-box;}
  html,body{height:100%;overflow:hidden;
    background:radial-gradient(120% 120% at 50% 30%,#241a10 0%,#140d07 60%,#080503 100%);}
  body{display:flex;flex-direction:column;align-items:center;justify-content:center;
    font-family:'Futura','Helvetica Neue',sans-serif;font-weight:300;color:#e8dcbf;
    -webkit-font-smoothing:antialiased;-webkit-user-select:none;user-select:none;}
  .brand{letter-spacing:.6em;font-size:1.7vmin;color:#a3844e;text-transform:uppercase;
    padding-left:.6em;margin-bottom:2.6vmin;text-shadow:0 0 12px rgba(255,181,82,.35);}
  .rack{display:flex;align-items:flex-start;justify-content:center;gap:2.4vw;width:96vw;}
  .meter{display:flex;flex-direction:column;align-items:center;flex:1;max-width:33vw;}
  .panel{width:100%;filter:drop-shadow(0 0 3vmin rgba(255,150,40,.18)) drop-shadow(0 2vmin 3vmin rgba(0,0,0,.6));}
  svg{display:block;width:100%;height:auto;}
  .readout{margin-top:1.6vmin;text-align:center;}
  .val{font-size:3.4vmin;letter-spacing:.05em;color:#f3e8cb;font-variant-numeric:tabular-nums;
    text-shadow:0 0 1.4vmin rgba(255,181,82,.35);}
  .val .u{font-size:.5em;color:#a3844e;letter-spacing:.14em;margin-left:.25em;text-shadow:none;}
  .sub{font-size:1.5vmin;letter-spacing:.24em;color:#8a7448;text-transform:uppercase;margin-top:.7vmin;}
  .foot{position:fixed;bottom:2.2vmin;left:0;right:0;text-align:center;
    font-size:1.4vmin;letter-spacing:.3em;color:#8a7448;text-transform:uppercase;}
  .foot b{color:#e8dcbf;font-weight:400;}
</style></head><body>
<div class="brand">Gauge</div>
<div class="rack">
  <div class="meter" id="m-mem"><div class="panel"></div>
    <div class="readout"><div class="val">--</div><div class="sub">Memory</div></div></div>
  <div class="meter" id="m-cpu"><div class="panel"></div>
    <div class="readout"><div class="val">--</div><div class="sub">CPU</div></div></div>
  <div class="meter" id="m-disk"><div class="panel"></div>
    <div class="readout"><div class="val">--</div><div class="sub">Disk</div></div></div>
</div>
<div class="foot"><span id="f-chip">--</span> &nbsp;·&nbsp; <b id="f-cores">--</b> CORES &nbsp;·&nbsp; <b id="f-ram">--</b> GB &nbsp;·&nbsp; <span id="clock">--</span></div>
<script>
var PX=154,PY=214,R=150;
function d2r(d){return d*Math.PI/180;}
function VP(r,d){return [PX+r*Math.cos(d2r(d)),PY+r*Math.sin(d2r(d))];}
function vA(f){f=Math.max(0,Math.min(1,f));return -125+f*70;}
function vArc(r,f0,f1){var p0=VP(r,vA(f0)),p1=VP(r,vA(f1));
  return 'M '+p0[0]+' '+p0[1]+' A '+r+' '+r+' 0 0 1 '+p1[0]+' '+p1[1];}

function buildVU(cfg){
  var ticks='',nums='',i,f,a,p0,p1,tp;
  for(i=0;i<=cfg.minor;i++){f=i/cfg.minor;a=vA(f);p0=VP(R,a);p1=VP(R-6,a);
    ticks+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="#8a7a52" stroke-width="1"/>';}
  for(i=0;i<cfg.majors.length;i++){var m=cfg.majors[i];a=vA(m.f);
    var red=cfg.redBand&&m.f>=cfg.redBand[0]-1e-6&&m.f<=cfg.redBand[1]+1e-6;var col=red?'var(--red)':'var(--scale)';
    p0=VP(R,a);p1=VP(R-11,a);tp=VP(R-22,a);
    ticks+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="'+col+'" stroke-width="2.2" stroke-linecap="round"/>';
    nums+='<text x="'+tp[0]+'" y="'+(tp[1]+4)+'" text-anchor="middle" font-size="12" fill="'+col+'">'+m.label+'</text>';}
  var redZone=cfg.redBand?'<path d="'+vArc(R+3,cfg.redBand[0],cfg.redBand[1])+'" stroke="var(--red)" stroke-width="3.5" fill="none"/>':'';
  var peak=cfg.peakLed?'<circle class="peakled" cx="278" cy="30" r="5" fill="#3a0f0a"/>'
    +'<text x="278" y="48" text-anchor="middle" font-size="7" letter-spacing="1.5" fill="#8a7448">PEAK</text>':'';
  var batt=cfg.battery?('<g transform="translate(40 34)">'
    +'<rect x="-15" y="-6" width="26" height="12" rx="2.4" fill="none" stroke="#8a7448" stroke-width="1.2"/>'
    +'<rect x="11" y="-2.6" width="2.4" height="5.2" rx="1" fill="#8a7448"/>'
    +'<rect class="battfill" x="-12.5" y="-3.6" width="21" height="7.2" rx="1" fill="#2f7d1f"/>'
    +'<path class="battbolt" d="M 1 -4.5 L -3 0.5 L 0 0.5 L -1.5 4.8 L 3 -0.8 L 0.5 -0.8 Z" fill="#0a2410"/>'
    +'<text x="-2" y="16" text-anchor="middle" font-size="7.5" fill="#8a7448">BATTERY</text></g>'):'';
  var peakNeedle=cfg.dual?'<g class="needle2"><polygon points="'+(PX+R-24)+','+PY+' '+(PX-8)+','+(PY-0.9)+' '+(PX-8)+','+(PY+0.9)+'" fill="var(--red)"/></g>':'';
  return '<svg viewBox="0 0 308 196"><defs>'
    +'<radialGradient id="glass_'+cfg.id+'" cx="50%" cy="86%" r="86%">'
    +'<stop offset="0%" stop-color="#fff4d8"/><stop offset="42%" stop-color="#f0e5c6"/><stop offset="100%" stop-color="#d8c79c"/></radialGradient>'
    +'<radialGradient id="warm_'+cfg.id+'" cx="50%" cy="92%" r="70%">'
    +'<stop offset="0%" stop-color="rgba(255,196,110,.55)"/><stop offset="100%" stop-color="rgba(255,196,110,0)"/></radialGradient>'
    +'<linearGradient id="bez_'+cfg.id+'" x1="0" y1="0" x2="0" y2="1">'
    +'<stop offset="0%" stop-color="#3a3128"/><stop offset="100%" stop-color="#17120c"/></linearGradient></defs>'
    +'<rect x="2" y="2" width="304" height="192" rx="10" fill="url(#bez_'+cfg.id+')" stroke="#0c0906" stroke-width="1.5"/>'
    +'<rect x="12" y="12" width="284" height="172" rx="7" fill="url(#glass_'+cfg.id+')"/>'
    +'<ellipse cx="154" cy="180" rx="150" ry="90" fill="url(#warm_'+cfg.id+')"/>'
    +redZone+ticks+nums
    +'<text x="154" y="150" text-anchor="middle" font-size="11" letter-spacing="4" fill="var(--scale)" opacity="0.85">'+cfg.name+'</text>'
    +'<text x="154" y="166" text-anchor="middle" font-size="7.5" letter-spacing="2.5" fill="var(--dim)">'+(cfg.unit||'')+'</text>'
    +peak+batt+peakNeedle
    +'<g class="needle"><polygon points="'+(PX+R-6)+','+PY+' '+(PX-8)+','+(PY-1.3)+' '+(PX-8)+','+(PY+1.3)+'" fill="#171008"/></g>'
    +'<circle cx="154" cy="214" r="9" fill="#171008"/></svg>';
}

var CPU={host:'#m-cpu',cfg:{id:'cpu',name:'CPU',unit:'% PROCESSOR LOAD',minor:40,redBand:[0.85,1],peakLed:true,dual:true,
  majors:[0,20,40,60,80,100].map(function(n){return {f:n/100,label:String(n)};})}};
var MEM={host:'#m-mem',cfg:{id:'mem',name:'MEMORY',unit:'% USED',minor:40,redBand:[0.85,1],
  majors:[0,20,40,60,80,100].map(function(n){return {f:n/100,label:String(n)};})}};
var DISK={host:'#m-disk',cfg:{id:'disk',name:'DISK',unit:'% FREE SPACE',minor:40,redBand:[0,0.15],battery:true,
  majors:[0,20,40,60,80,100].map(function(n){return {f:n/100,label:String(n)};})}};

function mount(g){var host=document.querySelector(g.host+' .panel');host.innerHTML=buildVU(g.cfg);
  g.needle=host.querySelector('.needle');g.needle2=host.querySelector('.needle2');g.peakled=host.querySelector('.peakled');
  g.battfill=host.querySelector('.battfill');g.battbolt=host.querySelector('.battbolt');
  g.valEl=document.querySelector(g.host+' .val');g.subEl=document.querySelector(g.host+' .sub');g.cur=0;g.peak=0;}
[MEM,CPU,DISK].forEach(mount);
function setN(node,f){node.setAttribute('transform','rotate('+vA(f)+' '+PX+' '+PY+')');}

var tgt={overall:0,peak:0,mem:0,disk:0.5},tot={memTotal:0,diskTotal:0};
var battery={present:true,charge:1.0,charging:true},frame=0;

function poll(){
  var x=new XMLHttpRequest();x.open('GET','/stats?t='+Date.now(),true);
  x.onreadystatechange=function(){
    if(x.readyState===4&&x.status===200){try{var s=JSON.parse(x.responseText);
      tgt.overall=s.cpu.overall;tgt.peak=s.cpu.peak;tgt.mem=s.mem.used_frac;tgt.disk=s.disk.free_frac;
      tot.memTotal=s.mem.total_gb;tot.diskTotal=s.disk.total_gb;battery=s.battery;
      document.getElementById('f-chip').textContent=s.sys.chip;
      document.getElementById('f-cores').textContent=s.sys.cores;
      document.getElementById('f-ram').textContent=Math.round(s.mem.total_gb);
    }catch(e){}}
  };x.send();
}
poll();setInterval(poll,1000);

// needle ballistics — lower = slower/heavier, more meter-like. Peak rises fast
// (catch a spike), falls slowly (meter-style decay).
var EASE=0.035, EASE_SLOW=0.06, PEAK_ATTACK=0.30, PEAK_RELEASE=0.035;
function animate(){
  frame++;
  CPU.cur+=(tgt.overall-CPU.cur)*EASE;
  var dP=tgt.peak-CPU.peak; CPU.peak+=dP*(dP>0?PEAK_ATTACK:PEAK_RELEASE);
  MEM.cur+=(tgt.mem-MEM.cur)*EASE_SLOW;DISK.cur+=(tgt.disk-DISK.cur)*EASE_SLOW;
  setN(CPU.needle,CPU.cur);setN(MEM.needle,MEM.cur);setN(DISK.needle,DISK.cur);
  if(CPU.needle2)setN(CPU.needle2,CPU.peak);
  if(CPU.peakled){var hot=CPU.peak>0.85;CPU.peakled.setAttribute('fill',hot?'#ff3b2a':'#3a0f0a');
    CPU.peakled.setAttribute('opacity',hot?(0.6+0.4*Math.abs(Math.sin(frame*0.3))):1);}
  if(DISK.battfill){var bc=Math.max(0,Math.min(1,battery.charge));
    DISK.battfill.setAttribute('width',(21*bc).toFixed(1));
    DISK.battfill.setAttribute('fill',bc<0.15?'var(--red)':'#2f7d1f');
    DISK.battbolt.setAttribute('opacity',battery.charging?1:0);}
  CPU.valEl.innerHTML=Math.round(CPU.cur*100)+'<span class="u">%</span>';
  CPU.subEl.textContent='peak '+Math.round(CPU.peak*100)+'%';
  MEM.valEl.innerHTML=(MEM.cur*tot.memTotal).toFixed(1)+'<span class="u">GB</span>';
  MEM.subEl.textContent=Math.round(MEM.cur*100)+'% of '+Math.round(tot.memTotal);
  DISK.valEl.innerHTML=Math.round(DISK.cur*100)+'<span class="u">%</span>';
  DISK.subEl.textContent=Math.round(DISK.cur*tot.diskTotal)+' GB free';
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
function clk(){var n=new Date(),h=n.getHours(),m=n.getMinutes();
  document.getElementById('clock').textContent=(h<10?'0':'')+h+':'+(m<10?'0':'')+m;}
clk();setInterval(clk,10000);
</script></body></html>"""


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
