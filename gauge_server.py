#!/usr/bin/env python3
"""
gauge_server.py — always-on LAN display server for the Gauge dials.

Serves a full-screen version of the gauge cluster over the local network so an
old iPad / iPhone / any browser can be left on as a dedicated dashboard.

Differences from gauge.py: binds 0.0.0.0 on a fixed port, never auto-quits,
and serves a responsive full-screen page (numbers inset in each dial). Reuses
gauge.py's pure-stdlib stat sampler.

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
  :root{--ink:#fff;--dim:#565656;--dim2:#8c8c8c;--red:#ff3b30;--green:#32d74b;}
  *{margin:0;padding:0;box-sizing:border-box;}
  html,body{height:100%;background:#000;overflow:hidden;}
  body{display:flex;flex-direction:column;align-items:center;justify-content:center;
    font-family:'Helvetica Neue',Inter,system-ui,sans-serif;font-weight:300;color:var(--ink);
    -webkit-font-smoothing:antialiased;-webkit-user-select:none;user-select:none;}
  .brand{letter-spacing:.6em;font-size:1.7vmin;color:var(--dim2);text-transform:uppercase;
    padding-left:.6em;margin-bottom:2.4vmin;}
  .cluster{display:flex;align-items:center;justify-content:center;gap:2.5vmin;}
  .gauge{display:flex;flex-direction:column;align-items:center;}
  .gauge.side .dial{width:30vmin;height:30vmin;}
  .gauge.center .dial{width:44vmin;height:44vmin;}
  .gauge.side{transform:translateY(3vmin);}
  .dial{position:relative;filter:drop-shadow(0 1.5vmin 3vmin rgba(0,0,0,.7));}
  svg{display:block;width:100%;height:100%;}
  .foot{position:fixed;bottom:2.2vmin;left:0;right:0;text-align:center;
    font-size:1.4vmin;letter-spacing:.3em;color:var(--dim);text-transform:uppercase;}
  .foot b{color:var(--dim2);font-weight:400;}
</style></head><body>
<div class="brand">Gauge</div>
<div class="cluster">
  <div class="gauge side" id="gauge-mem"><div class="dial"></div></div>
  <div class="gauge center" id="gauge-cpu"><div class="dial"></div></div>
  <div class="gauge side" id="gauge-disk"><div class="dial"></div></div>
</div>
<div class="foot"><span id="f-chip">--</span> &nbsp;·&nbsp; <b id="f-cores">--</b> CORES &nbsp;·&nbsp; <b id="f-ram">--</b> GB &nbsp;·&nbsp; <span id="clock">--</span></div>
<script>
var CX=150,CY=150,START=135,SWEEP=270;
function d2r(d){return d*Math.PI/180;}
function polar(r,d){return [CX+r*Math.cos(d2r(d)),CY+r*Math.sin(d2r(d))];}
function angleFor(f){f=Math.max(0,Math.min(1,f));return START+f*SWEEP;}
function arcPath(r,f0,f1){var a0=angleFor(f0),a1=angleFor(f1),p0=polar(r,a0),p1=polar(r,a1);
  return 'M '+p0[0]+' '+p0[1]+' A '+r+' '+r+' 0 '+((a1-a0)>180?1:0)+' 1 '+p1[0]+' '+p1[1];}

function buildDial(cfg){
  var ticks='',nums='',i,f,a,p0,p1,tp;
  for(i=0;i<=cfg.minor;i++){f=i/cfg.minor;a=angleFor(f);p0=polar(122,a);p1=polar(116,a);
    ticks+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="#3a3a3a" stroke-width="1"/>';}
  for(i=0;i<cfg.majors.length;i++){var m=cfg.majors[i];a=angleFor(m.f);
    var red=cfg.redBand&&m.f>=cfg.redBand[0]-1e-6&&m.f<=cfg.redBand[1]+1e-6;var col=red?'var(--red)':'var(--ink)';
    p0=polar(123,a);p1=polar(107,a);tp=polar(90,a);
    ticks+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="'+col+'" stroke-width="1.6" stroke-linecap="round"/>';
    nums+='<text x="'+tp[0]+'" y="'+(tp[1]+5)+'" text-anchor="middle" font-size="15" font-weight="300" fill="'+col+'">'+m.label+'</text>';}
  var red=cfg.redBand?'<path d="'+arcPath(124,cfg.redBand[0],cfg.redBand[1])+'" stroke="var(--red)" stroke-width="4" fill="none"/>':'';
  var innerTrack=cfg.inner?('<path d="'+arcPath(76,0,1)+'" stroke="#191919" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
    +'<text x="150" y="171" text-anchor="middle" font-size="7.5" letter-spacing="2" fill="#565656">PEAK CORE</text>'):'';
  var innerNeedle=cfg.inner?'<g class="needle2"><polygon points="216,150 150,149.1 150,150.9" fill="var(--red)"/></g>':'';
  var battOutline=cfg.battery?('<g transform="translate(150 168)">'
    +'<text x="0" y="-10" text-anchor="middle" font-size="7" letter-spacing="1.6" fill="#8c8c8c">BATTERY</text>'
    +'<rect x="-13" y="-6" width="24" height="12" rx="2.4" fill="none" stroke="#8c8c8c" stroke-width="1.1"/>'
    +'<rect x="11" y="-2.6" width="2.4" height="5.2" rx="1" fill="#8c8c8c"/>'
    +'<rect class="battfill" x="-10.5" y="-3.6" width="19" height="7.2" rx="1" fill="var(--green)"/>'
    +'<path class="battbolt" d="M 1.3 -4.5 L -2.7 0.4 L 0 0.4 L -1.3 4.5 L 3.2 -0.9 L 0.4 -0.9 Z" fill="#04270f"/></g>'):'';
  return '<svg viewBox="0 0 300 300">'
    +'<circle cx="150" cy="150" r="147" fill="none" stroke="#2a2a2a" stroke-width="1"/>'
    +'<circle cx="150" cy="150" r="143" fill="none" stroke="#161616" stroke-width="1.5"/>'
    +'<circle cx="150" cy="150" r="140" fill="#080808"/>'
    +red+ticks+nums+innerTrack+battOutline
    +'<text x="150" y="116" text-anchor="middle" font-size="11" letter-spacing="4" fill="#8c8c8c">'+cfg.faceName+'</text>'
    +innerNeedle
    +'<g class="needle"><polygon points="150,150 124,148.8 124,151.2" fill="#3a3a3a"/>'
    +'<polygon points="256,150 166,149 166,151" fill="var(--ink)"/>'
    +'<polygon points="256,150 238,149.7 238,150.3" fill="var(--red)"/></g>'
    +'<circle cx="150" cy="150" r="6.5" fill="#e8e8e8"/><circle cx="150" cy="150" r="2.4" fill="#000"/>'
    +'<text class="val" x="150" y="228" text-anchor="middle" font-size="30" font-weight="300" fill="#fff"></text>'
    +'<text class="sub" x="150" y="248" text-anchor="middle" font-size="12" fill="#6a6a6a" letter-spacing="1.2"></text>'
    +'</svg>';
}

var CPU={el:'#gauge-cpu',cfg:{faceName:'CPU',redBand:[0.85,1],minor:50,inner:true,
  majors:[0,1,2,3,4,5,6,7,8,9,10].map(function(n){return {f:n/10,label:String(n)};})}};
var MEM={el:'#gauge-mem',cfg:{faceName:'MEM',redBand:[0.85,1],minor:50,
  majors:[0,20,40,60,80,100].map(function(n){return {f:n/100,label:String(n)};})}};
var DISK={el:'#gauge-disk',cfg:{faceName:'DISK',redBand:[0,0.15],minor:40,battery:true,
  majors:[{f:0,label:'0'},{f:0.5,label:'50'},{f:1,label:'100'}]}};

function mount(g){var host=document.querySelector(g.el+' .dial');host.innerHTML=buildDial(g.cfg);
  g.needle=host.querySelector('.needle');g.needle2=host.querySelector('.needle2');
  g.battfill=host.querySelector('.battfill');g.battbolt=host.querySelector('.battbolt');
  g.valEl=host.querySelector('.val');g.subEl=host.querySelector('.sub');g.cur=0;g.peak=0;}
[MEM,CPU,DISK].forEach(mount);
function setN(g,f){g.needle.setAttribute('transform','rotate('+angleFor(f)+' 150 150)');}

var tgt={overall:0,peak:0,mem:0,disk:0.5};
var tot={memTotal:0,diskTotal:0};
var battery={present:true,charge:1.0,charging:true};

function poll(){
  var x=new XMLHttpRequest();
  x.open('GET','/stats?t='+Date.now(),true);
  x.onreadystatechange=function(){
    if(x.readyState===4&&x.status===200){
      try{var s=JSON.parse(x.responseText);
        tgt.overall=s.cpu.overall;tgt.peak=s.cpu.peak;tgt.mem=s.mem.used_frac;tgt.disk=s.disk.free_frac;
        tot.memTotal=s.mem.total_gb;tot.diskTotal=s.disk.total_gb;battery=s.battery;
        document.getElementById('f-chip').textContent=s.sys.chip;
        document.getElementById('f-cores').textContent=s.sys.cores;
        document.getElementById('f-ram').textContent=Math.round(s.mem.total_gb);
      }catch(e){}
    }
  };
  x.send();
}
poll();setInterval(poll,1000);

function animate(){
  CPU.cur+=(tgt.overall-CPU.cur)*0.12;CPU.peak+=(tgt.peak-CPU.peak)*0.30;
  MEM.cur+=(tgt.mem-MEM.cur)*0.12;DISK.cur+=(tgt.disk-DISK.cur)*0.12;
  setN(MEM,MEM.cur);setN(CPU,CPU.cur);setN(DISK,DISK.cur);
  if(CPU.needle2)CPU.needle2.setAttribute('transform','rotate('+angleFor(Math.min(1,CPU.peak))+' 150 150)');
  if(DISK.battfill){var bc=Math.max(0,Math.min(1,battery.charge));
    DISK.battfill.setAttribute('width',(19*bc).toFixed(1));
    DISK.battfill.setAttribute('fill',bc<0.15?'var(--red)':'var(--green)');
    DISK.battbolt.setAttribute('opacity',battery.charging?1:0);}
  CPU.valEl.innerHTML=Math.round(CPU.cur*100)+'<tspan font-size="15" fill="#8c8c8c" dx="2">%</tspan>';
  CPU.subEl.textContent='peak '+Math.round(CPU.peak*100)+'%';
  MEM.valEl.innerHTML=(MEM.cur*tot.memTotal).toFixed(1)+'<tspan font-size="15" fill="#8c8c8c" dx="2">GB</tspan>';
  MEM.subEl.textContent=Math.round(MEM.cur*100)+'% of '+Math.round(tot.memTotal);
  DISK.valEl.innerHTML=Math.round(DISK.cur*100)+'<tspan font-size="15" fill="#8c8c8c" dx="2">%</tspan>';
  DISK.subEl.textContent=Math.round(DISK.cur*tot.diskTotal)+' GB free';
  requestAnimationFrame(animate);
}
requestAnimationFrame(animate);
function clk(){var n=new Date();var h=n.getHours(),m=n.getMinutes();
  document.getElementById('clock').textContent=(h<10?'0':'')+h+':'+(m<10?'0':'')+m;}
clk();setInterval(clk,10000);
</script></body></html>"""


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
