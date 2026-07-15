/* Gauge web engine — builds the chosen view and drives it from /stats.
   window.GV selects the view: 'minimal' | 'vintage' | 'vu' | 'pair'. */
(function(){
var GV = window.GV || 'minimal';

/* ---------- shared round-dial geometry ---------- */
function d2r(d){return d*Math.PI/180;}
function clamp(f){return Math.max(0,Math.min(1,f));}
function polar(cx,cy,r,d){return [cx+r*Math.cos(d2r(d)), cy+r*Math.sin(d2r(d))];}
var START=135, SWEEP=270;
function aF(f){return START+clamp(f)*SWEEP;}
function rarc(cx,cy,r,f0,f1){var a0=aF(f0),a1=aF(f1),p0=polar(cx,cy,r,a0),p1=polar(cx,cy,r,a1);
  return 'M '+p0[0]+' '+p0[1]+' A '+r+' '+r+' 0 '+((a1-a0)>180?1:0)+' 1 '+p1[0]+' '+p1[1];}

/* ---------- live stats ---------- */
var S=null;
function poll(){var x=new XMLHttpRequest();x.open('GET','/stats?t='+(+new Date()),true);
  x.onreadystatechange=function(){if(x.readyState===4&&x.status===200){try{S=JSON.parse(x.responseText);}catch(e){}}};x.send();}
poll(); setInterval(poll,1000);
function foot(){ if(!S)return;
  var c=document.getElementById('f-chip'),co=document.getElementById('f-cores'),r=document.getElementById('f-ram');
  if(c)c.textContent=S.sys.chip; if(co)co.textContent=S.sys.cores; if(r)r.textContent=Math.round(S.mem.total_gb); }
function clock(){var el=document.getElementById('clock'); if(!el)return;
  var n=new Date(),h=n.getHours(),m=n.getMinutes(); el.textContent=(h<10?'0':'')+h+':'+(m<10?'0':'')+m; }
setInterval(clock,10000);

/* ---------- dispatch ---------- */
if(GV==='vu') initVU();
else if(GV==='pair') initPair();
else initRound(GV);

/* ========== ROUND (minimal / vintage) ========== */
function initRound(theme){
  var vintage = theme==='vintage';
  function dial(cfg){
    var ticks='',nums='',i,f,a,p0,p1,tp,m;
    for(i=0;i<=cfg.minor;i++){f=i/cfg.minor;a=aF(f);p0=polar(150,150,122,a);p1=polar(150,150,116,a);
      ticks+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="'+(vintage?'#4a463c':'#3a3a3a')+'" stroke-width="1"/>';}
    for(i=0;i<cfg.majors.length;i++){m=cfg.majors[i];a=aF(m.f);
      var red=cfg.redBand&&m.f>=cfg.redBand[0]-1e-6&&m.f<=cfg.redBand[1]+1e-6;var col=red?'var(--red)':'var(--ink)';
      p0=polar(150,150,123,a);p1=polar(150,150,107,a);tp=polar(150,150,vintage?88:90,a);
      ticks+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="'+col+'" stroke-width="'+(vintage?2.6:1.6)+'" stroke-linecap="round"/>';
      nums+='<text x="'+tp[0]+'" y="'+(tp[1]+5)+'" text-anchor="middle" font-size="'+(vintage?17:15)+'" fill="'+col+'" font-weight="300">'+m.label+'</text>';}
    var guil='';
    if(vintage){for(var r=44;r<=116;r+=9)guil+='<circle cx="150" cy="150" r="'+r+'" fill="none" stroke="#141414" stroke-width="0.6"/>';}
    var red=cfg.redBand?'<path d="'+rarc(150,150,124,cfg.redBand[0],cfg.redBand[1])+'" stroke="var(--red)" stroke-width="'+(vintage?6:4)+'" fill="none"/>':'';
    var batt='';
    if(cfg.battery)batt='<g transform="translate(150 176)">'
      +'<text x="0" y="-11" text-anchor="middle" font-size="7" letter-spacing="1.8" fill="var(--dim2)">BATTERY</text>'
      +'<rect x="-14" y="-6.5" width="26" height="13" rx="2.5" fill="none" stroke="var(--dim2)" stroke-width="1.2"/>'
      +'<rect x="12" y="-3" width="2.6" height="6" rx="1" fill="var(--dim2)"/>'
      +'<rect class="battfill" x="-11.5" y="-4" width="21" height="8" rx="1" fill="var(--green)"/>'
      +'<path class="battbolt" d="M 1.5 -5 L -3 0.5 L 0 0.5 L -1.5 5 L 3.5 -1 L 0.5 -1 Z" fill="#04270f"/>'
      +'<text class="battpct" x="0" y="19" text-anchor="middle" font-size="8" fill="var(--dim2)">--</text></g>';
    var it='',iN='';
    if(cfg.inner){
      it='<path d="'+rarc(150,150,76,0,1)+'" stroke="'+(vintage?'#201d16':'#191919')+'" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
        +'<path class="innerfill" d="'+rarc(150,150,76,0,0.002)+'" stroke="var(--accent)" stroke-width="3.5" fill="none" stroke-linecap="round"/>'
        +'<text x="150" y="176" text-anchor="middle" font-size="7.5" letter-spacing="2" fill="var(--dim)">PEAK CORE</text>';
      iN='<g class="needle2" transform="rotate('+aF(0)+' 150 150)"><polygon points="216,150 150,149.1 150,150.9" fill="var(--red)"/></g>';
    }
    var fn=cfg.faceName, defs, bez, hub, needle;
    if(vintage){
      defs='<defs><radialGradient id="bz_'+fn+'" cx="42%" cy="34%" r="72%"><stop offset="0%" stop-color="#f2f2f2"/><stop offset="20%" stop-color="#c2c2c2"/><stop offset="46%" stop-color="#5f5f5f"/><stop offset="72%" stop-color="#d0d0d0"/><stop offset="90%" stop-color="#454545"/><stop offset="100%" stop-color="#1e1e1e"/></radialGradient>'
        +'<radialGradient id="fc_'+fn+'" cx="50%" cy="40%" r="75%"><stop offset="0%" stop-color="#1a1a1a"/><stop offset="65%" stop-color="#0d0d0d"/><stop offset="100%" stop-color="#040404"/></radialGradient>'
        +'<radialGradient id="hb_'+fn+'" cx="40%" cy="34%" r="70%"><stop offset="0%" stop-color="#f4f4f4"/><stop offset="48%" stop-color="#9a9a9a"/><stop offset="100%" stop-color="#242424"/></radialGradient></defs>';
      bez='<circle cx="150" cy="150" r="148" fill="url(#bz_'+fn+')"/><circle cx="150" cy="150" r="134" fill="#0a0a0a"/><circle cx="150" cy="150" r="131" fill="url(#fc_'+fn+')"/>';
      hub='<circle cx="150" cy="150" r="15" fill="url(#hb_'+fn+')"/><circle cx="150" cy="150" r="4.5" fill="#141414"/>';
      needle='<g class="needle" transform="rotate('+aF(0)+' 150 150)"><polygon points="150,150 120,148.2 120,151.8" fill="#e8e4d8"/><polygon points="256,150 162,148.6 162,151.4" fill="var(--ink)"/><polygon points="256,150 232,149.5 232,150.5" fill="var(--red)"/></g>';
    }else{
      defs='<defs><radialGradient id="fc_'+fn+'" cx="50%" cy="42%" r="72%"><stop offset="0%" stop-color="#0e0e0e"/><stop offset="70%" stop-color="#070707"/><stop offset="100%" stop-color="#000"/></radialGradient></defs>';
      bez='<circle cx="150" cy="150" r="147" fill="none" stroke="#2a2a2a" stroke-width="1"/><circle cx="150" cy="150" r="143" fill="none" stroke="#161616" stroke-width="1.5"/><circle cx="150" cy="150" r="140" fill="url(#fc_'+fn+')"/>';
      hub='<circle cx="150" cy="150" r="6.5" fill="#e8e8e8"/><circle cx="150" cy="150" r="2.4" fill="#000"/>';
      needle='<g class="needle" transform="rotate('+aF(0)+' 150 150)"><polygon points="150,150 124,148.8 124,151.2" fill="#3a3a3a"/><polygon points="256,150 166,149 166,151" fill="var(--ink)"/><polygon points="256,150 238,149.7 238,150.3" fill="var(--red)"/></g>';
    }
    return '<svg viewBox="0 0 300 300">'+defs+bez+guil+red+ticks+nums+batt+it
      +'<text x="150" y="'+(vintage?118:120)+'" text-anchor="middle" font-size="'+(vintage?12:11)+'" letter-spacing="'+(vintage?3.5:4)+'" fill="var(--dim2)">'+cfg.faceName+'</text>'
      +'<text x="150" y="'+(vintage?208:210)+'" text-anchor="middle" font-size="'+(vintage?9:8.5)+'" letter-spacing="2.5" fill="var(--dim)">'+(cfg.faceUnit||'')+'</text>'
      +iN+needle+hub+'</svg>';
  }
  var CPU={el:'gc',cfg:{faceName:'CPU',faceUnit:'× 10 %  OVERALL',redBand:[0.85,1],minor:50,inner:true,
    majors:[0,1,2,3,4,5,6,7,8,9,10].map(function(n){return {f:n/10,label:String(n)};})}};
  var MEM={el:'gm',cfg:{faceName:'MEM',faceUnit:'% USED',redBand:[0.85,1],minor:50,
    majors:[0,20,40,60,80,100].map(function(n){return {f:n/100,label:String(n)};})}};
  var DISK={el:'gd',cfg:{faceName:'DISK',faceUnit:'% FREE',redBand:[0,0.15],minor:40,battery:true,
    majors:[{f:0,label:'0'},{f:0.5,label:'50'},{f:1,label:'100'}]}};
  var app=document.getElementById('app');
  app.innerHTML='<div class="brand">Gauge</div><div class="cluster">'
    +'<div class="gauge side" id="mem"><div class="dial"></div><div class="readout"><div class="val">--</div><div class="sub">Memory</div></div></div>'
    +'<div class="gauge center" id="cpu"><div class="dial"></div><div class="readout"><div class="val">--</div><div class="sub">CPU</div></div></div>'
    +'<div class="gauge side" id="disk"><div class="dial"></div><div class="readout"><div class="val">--</div><div class="sub">Disk</div></div></div></div>'
    +'<div class="foot"><span id="f-chip">--</span> &nbsp;·&nbsp; <b id="f-cores">--</b> CORES &nbsp;·&nbsp; <b id="f-ram">--</b> GB &nbsp;·&nbsp; <span id="clock">--</span></div>';
  function mount(g,pid){var host=document.querySelector('#'+pid+' .dial');host.innerHTML=dial(g.cfg);
    g.needle=host.querySelector('.needle');g.needle2=host.querySelector('.needle2');g.innerfill=host.querySelector('.innerfill');
    g.battfill=host.querySelector('.battfill');g.battbolt=host.querySelector('.battbolt');g.battpct=host.querySelector('.battpct');
    g.valEl=document.querySelector('#'+pid+' .val');g.subEl=document.querySelector('#'+pid+' .sub');g.cur=0;g.peak=0;}
  mount(MEM,'mem');mount(CPU,'cpu');mount(DISK,'disk');
  function setN(g,f){g.needle.setAttribute('transform','rotate('+aF(f)+' 150 150)');}
  clock();
  function animate(){
    if(S){
      CPU.cur+=(S.cpu.overall-CPU.cur)*0.22;CPU.peak+=(S.cpu.peak-CPU.peak)*0.42;
      MEM.cur+=(S.mem.used_frac-MEM.cur)*0.20;DISK.cur+=(S.disk.free_frac-DISK.cur)*0.20;
      setN(MEM,MEM.cur);setN(CPU,CPU.cur);setN(DISK,DISK.cur);
      CPU.needle2.setAttribute('transform','rotate('+aF(Math.min(1,CPU.peak))+' 150 150)');
      CPU.innerfill.setAttribute('d',rarc(150,150,76,0,Math.max(0.002,Math.min(1,CPU.peak))));
      CPU.innerfill.setAttribute('stroke',CPU.peak>0.85?'var(--red)':'var(--accent)');
      var b=S.battery,bc=clamp(b.charge);
      DISK.battfill.setAttribute('width',(21*bc).toFixed(1));
      DISK.battfill.setAttribute('fill',bc<0.15?'var(--red)':'var(--green)');
      DISK.battbolt.setAttribute('opacity',b.charging?1:0);DISK.battpct.textContent=Math.round(bc*100)+'%';
      CPU.valEl.innerHTML=Math.round(CPU.cur*100)+'<span class="u">%</span>';CPU.subEl.textContent='peak '+Math.round(CPU.peak*100)+'%';
      MEM.valEl.innerHTML=(MEM.cur*S.mem.total_gb).toFixed(1)+'<span class="u">GB</span>';MEM.subEl.textContent=Math.round(MEM.cur*100)+'% of '+Math.round(S.mem.total_gb);
      DISK.valEl.innerHTML=Math.round(DISK.cur*100)+'<span class="u">%</span>';DISK.subEl.textContent=Math.round(DISK.cur*S.disk.total_gb)+' GB free';
      foot();
    }
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);
}

/* ========== VU METERS ========== */
function initVU(){
  var PX=154,PY=214,R=150;
  function VP(r,d){return [PX+r*Math.cos(d2r(d)),PY+r*Math.sin(d2r(d))];}
  function vA(f){return -125+clamp(f)*70;}
  function vArc(r,f0,f1){var p0=VP(r,vA(f0)),p1=VP(r,vA(f1));return 'M '+p0[0]+' '+p0[1]+' A '+r+' '+r+' 0 0 1 '+p1[0]+' '+p1[1];}
  function meter(cfg){
    var ticks='',nums='',i,f,a,p0,p1,tp,m;
    for(i=0;i<=cfg.minor;i++){f=i/cfg.minor;a=vA(f);p0=VP(R,a);p1=VP(R-6,a);
      ticks+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="#8a7a52" stroke-width="1"/>';}
    for(i=0;i<cfg.majors.length;i++){m=cfg.majors[i];a=vA(m.f);
      var red=cfg.redBand&&m.f>=cfg.redBand[0]-1e-6&&m.f<=cfg.redBand[1]+1e-6;var col=red?'var(--red)':'var(--scale)';
      p0=VP(R,a);p1=VP(R-11,a);tp=VP(R-22,a);
      ticks+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="'+col+'" stroke-width="2.2" stroke-linecap="round"/>';
      nums+='<text x="'+tp[0]+'" y="'+(tp[1]+4)+'" text-anchor="middle" font-size="12" fill="'+col+'">'+m.label+'</text>';}
    var rz=cfg.redBand?'<path d="'+vArc(R+3,cfg.redBand[0],cfg.redBand[1])+'" stroke="var(--red)" stroke-width="3.5" fill="none"/>':'';
    var pk=cfg.peakLed?'<circle class="peakled" cx="278" cy="30" r="5" fill="#3a0f0a"/><text x="278" y="48" text-anchor="middle" font-size="7" letter-spacing="1.5" fill="#8a7448">PEAK</text>':'';
    var batt=cfg.battery?'<g transform="translate(40 34)">'
      +'<rect x="-15" y="-6" width="26" height="12" rx="2.4" fill="none" stroke="#8a7448" stroke-width="1.2"/>'
      +'<rect x="11" y="-2.6" width="2.4" height="5.2" rx="1" fill="#8a7448"/>'
      +'<rect class="battfill" x="-12.5" y="-3.6" width="21" height="7.2" rx="1" fill="#2f7d1f"/>'
      +'<path class="battbolt" d="M 1 -4.5 L -3 0.5 L 0 0.5 L -1.5 4.8 L 3 -0.8 L 0.5 -0.8 Z" fill="#0a2410"/>'
      +'<text x="-2" y="16" text-anchor="middle" font-size="7.5" fill="#8a7448">BATTERY</text></g>':'';
    var pN=cfg.dual?'<g class="needle2"><polygon points="'+(PX+R-24)+','+PY+' '+(PX-8)+','+(PY-0.9)+' '+(PX-8)+','+(PY+0.9)+'" fill="var(--red)"/></g>':'';
    return '<svg viewBox="0 0 308 196"><defs>'
      +'<radialGradient id="gl_'+cfg.id+'" cx="50%" cy="86%" r="86%"><stop offset="0%" stop-color="#fff4d8"/><stop offset="42%" stop-color="#f0e5c6"/><stop offset="100%" stop-color="#d8c79c"/></radialGradient>'
      +'<radialGradient id="wm_'+cfg.id+'" cx="50%" cy="92%" r="70%"><stop offset="0%" stop-color="rgba(255,196,110,.55)"/><stop offset="100%" stop-color="rgba(255,196,110,0)"/></radialGradient>'
      +'<linearGradient id="bz_'+cfg.id+'" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#3a3128"/><stop offset="100%" stop-color="#17120c"/></linearGradient></defs>'
      +'<rect x="2" y="2" width="304" height="192" rx="10" fill="url(#bz_'+cfg.id+')" stroke="#0c0906" stroke-width="1.5"/>'
      +'<rect x="12" y="12" width="284" height="172" rx="7" fill="url(#gl_'+cfg.id+')"/>'
      +'<ellipse cx="154" cy="180" rx="150" ry="90" fill="url(#wm_'+cfg.id+')"/>'
      +rz+ticks+nums
      +'<text x="154" y="150" text-anchor="middle" font-size="11" letter-spacing="4" fill="var(--scale)" opacity="0.85">'+cfg.name+'</text>'
      +'<text x="154" y="166" text-anchor="middle" font-size="7.5" letter-spacing="2.5" fill="var(--dim)">'+(cfg.unit||'')+'</text>'
      +pk+batt+pN
      +'<g class="needle"><polygon points="'+(PX+R-6)+','+PY+' '+(PX-8)+','+(PY-1.3)+' '+(PX-8)+','+(PY+1.3)+'" fill="#171008"/></g>'
      +'<circle cx="154" cy="214" r="9" fill="#171008"/></svg>';
  }
  var CPU={host:'cpu',cfg:{id:'cpu',name:'CPU',unit:'% PROCESSOR LOAD',minor:40,redBand:[0.85,1],peakLed:true,dual:true,
    majors:[0,20,40,60,80,100].map(function(n){return {f:n/100,label:String(n)};})}};
  var MEM={host:'mem',cfg:{id:'mem',name:'MEMORY',unit:'% USED',minor:40,redBand:[0.85,1],
    majors:[0,20,40,60,80,100].map(function(n){return {f:n/100,label:String(n)};})}};
  var DISK={host:'disk',cfg:{id:'disk',name:'DISK',unit:'% FREE SPACE',minor:40,redBand:[0,0.15],battery:true,
    majors:[0,20,40,60,80,100].map(function(n){return {f:n/100,label:String(n)};})}};
  var app=document.getElementById('app');
  app.innerHTML='<div class="brand">Gauge</div><div class="rack">'
    +'<div class="meter" id="mem"><div class="panel"></div><div class="readout"><div class="val">--</div><div class="sub">Memory</div></div></div>'
    +'<div class="meter" id="cpu"><div class="panel"></div><div class="readout"><div class="val">--</div><div class="sub">CPU</div></div></div>'
    +'<div class="meter" id="disk"><div class="panel"></div><div class="readout"><div class="val">--</div><div class="sub">Disk</div></div></div></div>'
    +'<div class="foot"><span id="f-chip">--</span> &nbsp;·&nbsp; <b id="f-cores">--</b> CORES &nbsp;·&nbsp; <b id="f-ram">--</b> GB &nbsp;·&nbsp; <span id="clock">--</span></div>';
  function mount(g){var host=document.querySelector('#'+g.host+' .panel');host.innerHTML=meter(g.cfg);
    g.needle=host.querySelector('.needle');g.needle2=host.querySelector('.needle2');g.peakled=host.querySelector('.peakled');
    g.battfill=host.querySelector('.battfill');g.battbolt=host.querySelector('.battbolt');
    g.valEl=document.querySelector('#'+g.host+' .val');g.subEl=document.querySelector('#'+g.host+' .sub');g.cur=0;g.peak=0;}
  mount(MEM);mount(CPU);mount(DISK);
  function setN(node,f){node.setAttribute('transform','rotate('+vA(f)+' '+PX+' '+PY+')');}
  clock();
  var EASE=0.035,ES=0.06,PA=0.30,PR=0.035,frame=0;
  function animate(){
    frame++;
    if(S){
      CPU.cur+=(S.cpu.overall-CPU.cur)*EASE;var dP=S.cpu.peak-CPU.peak;CPU.peak+=dP*(dP>0?PA:PR);
      MEM.cur+=(S.mem.used_frac-MEM.cur)*ES;DISK.cur+=(S.disk.free_frac-DISK.cur)*ES;
      setN(CPU.needle,CPU.cur);setN(MEM.needle,MEM.cur);setN(DISK.needle,DISK.cur);
      if(CPU.needle2)setN(CPU.needle2,CPU.peak);
      if(CPU.peakled){var hot=CPU.peak>0.85;CPU.peakled.setAttribute('fill',hot?'#ff3b2a':'#3a0f0a');
        CPU.peakled.setAttribute('opacity',hot?(0.6+0.4*Math.abs(Math.sin(frame*0.3))):1);}
      var b=S.battery,bc=clamp(b.charge);
      DISK.battfill.setAttribute('width',(21*bc).toFixed(1));DISK.battfill.setAttribute('fill',bc<0.15?'var(--red)':'#2f7d1f');
      DISK.battbolt.setAttribute('opacity',b.charging?1:0);
      CPU.valEl.innerHTML=Math.round(CPU.cur*100)+'<span class="u">%</span>';CPU.subEl.textContent='peak '+Math.round(CPU.peak*100)+'%';
      MEM.valEl.innerHTML=(MEM.cur*S.mem.total_gb).toFixed(1)+'<span class="u">GB</span>';MEM.subEl.textContent=Math.round(MEM.cur*100)+'% of '+Math.round(S.mem.total_gb);
      DISK.valEl.innerHTML=Math.round(DISK.cur*100)+'<span class="u">%</span>';DISK.subEl.textContent=Math.round(DISK.cur*S.disk.total_gb)+' GB free';
      foot();
    }
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);
}

/* ========== PAIR (system chronograph + clock) ========== */
function initPair(){
  var P=function(cx,cy,r,deg){return [cx+r*Math.cos(d2r(deg)),cy+r*Math.sin(d2r(deg))];};
  function arc(cx,cy,r,f0,f1){var a0=aF(f0),a1=aF(f1),p0=P(cx,cy,r,a0),p1=P(cx,cy,r,a1);
    return 'M '+p0[0]+' '+p0[1]+' A '+r+' '+r+' 0 '+((a1-a0)>180?1:0)+' 1 '+p1[0]+' '+p1[1];}
  function sub(cx,cy,R,cfg,sfx){
    var ticks='',i,f,a,p0,p1;
    for(i=0;i<=cfg.majors;i++){f=i/cfg.majors;a=aF(f);var inRed=cfg.redBand&&f>=cfg.redBand[0]-1e-6&&f<=cfg.redBand[1]+1e-6;
      p0=P(cx,cy,R-2,a);p1=P(cx,cy,R-8,a);
      ticks+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="'+(inRed?'var(--red)':'var(--dim2)')+'" stroke-width="1.3"/>';}
    var red=cfg.redBand?'<path d="'+arc(cx,cy,R-1,cfg.redBand[0],cfg.redBand[1])+'" stroke="var(--red)" stroke-width="2" fill="none"/>':'';
    var bolt=cfg.bolt?'<path d="M '+(cx+1)+' '+(cy+6)+' L '+(cx-3)+' '+(cy+13)+' L '+cx+' '+(cy+13)+' L '+(cx-1.5)+' '+(cy+19)+' L '+(cx+4)+' '+(cy+11)+' L '+(cx+0.5)+' '+(cy+11)+' Z" fill="var(--lume)" transform="translate(0 -2)"/>':'';
    var hand=cfg.hand?'<g class="'+cfg.hand+'" transform="rotate('+aF(0)+' '+cx+' '+cy+')"><polygon points="'+(cx+R-10)+','+cy+' '+(cx-8)+','+(cy-1.4)+' '+(cx-8)+','+(cy+1.4)+'" fill="var(--ink)"/></g><circle cx="'+cx+'" cy="'+cy+'" r="3" fill="#cfcfcf"/><circle cx="'+cx+'" cy="'+cy+'" r="1.1" fill="#000"/>':'';
    var val=cfg.textId?'<text class="'+cfg.textId+'" x="'+cx+'" y="'+(cy+R*0.30)+'" text-anchor="middle" font-size="'+(cfg.big?17:12)+'" font-weight="400" fill="var(--ink)">--</text>':'';
    return '<circle cx="'+cx+'" cy="'+cy+'" r="'+R+'" fill="#0a0a0a" stroke="#242424" stroke-width="1"/>'
      +'<circle cx="'+cx+'" cy="'+cy+'" r="'+(R-3)+'" fill="url(#sf_'+sfx+')"/>'+red+ticks+bolt
      +'<text x="'+cx+'" y="'+(cy-R*0.42)+'" text-anchor="middle" font-size="8" letter-spacing="1.6" fill="var(--dim2)">'+cfg.name+'</text>'+hand+val;
  }
  function chassis(){var mk='',mn='',i,h,a,p0,p1;
    for(i=0;i<120;i++){a=i*3;p0=P(200,200,192,a);p1=P(200,200,i%10===0?185:188,a);
      mn+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="#2c2c2c" stroke-width="'+(i%10===0?1.1:0.6)+'"/>';}
    for(h=0;h<12;h++){if(h===3||h===6||h===9)continue;a=h*30-90;p0=P(200,200,176,a);p1=P(200,200,164,a);
      mk+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="var(--ink)" stroke-width="'+(h%3===0?3:2)+'" stroke-linecap="round"/>';}
    return mn+mk;}
  function shell(sfx,inner){return '<svg viewBox="0 0 400 400"><defs>'
    +'<radialGradient id="fc_'+sfx+'" cx="50%" cy="42%" r="70%"><stop offset="0%" stop-color="#141414"/><stop offset="70%" stop-color="#0a0a0a"/><stop offset="100%" stop-color="#020202"/></radialGradient>'
    +'<radialGradient id="sf_'+sfx+'" cx="50%" cy="40%" r="70%"><stop offset="0%" stop-color="#101010"/><stop offset="100%" stop-color="#040404"/></radialGradient>'
    +'<filter id="hs_'+sfx+'" x="-40%" y="-40%" width="180%" height="180%"><feDropShadow dx="0" dy="1.2" stdDeviation="1.6" flood-color="#000" flood-opacity="0.6"/></filter></defs>'
    +'<circle cx="200" cy="200" r="198" fill="#161616"/><circle cx="200" cy="200" r="192" fill="#080808" stroke="#2a2a2a" stroke-width="1"/><circle cx="200" cy="200" r="190" fill="url(#fc_'+sfx+')"/>'
    +chassis()+inner+'</svg>';}
  var gTicks='',i;
  for(i=0;i<=50;i++){var f=i/50,a=aF(f),p0=P(200,200,158,a),p1=P(200,200,i%5===0?146:152,a);
    gTicks+='<line x1="'+p0[0]+'" y1="'+p0[1]+'" x2="'+p1[0]+'" y2="'+p1[1]+'" stroke="'+(f>=0.85?'var(--red)':'#585858')+'" stroke-width="'+(i%5===0?1.6:0.9)+'"/>';}
  var gNums='';[0,40,60,100].forEach(function(n){var f=n/100,a=aF(f),tp=P(200,200,132,a);
    gNums+='<text x="'+tp[0]+'" y="'+(tp[1]+4)+'" text-anchor="middle" font-size="13" font-weight="300" fill="'+(f>=0.85?'var(--red)':'var(--ink)')+'">'+n+'</text>';});
  var gaugeInner='<path d="'+arc(200,200,160,0.85,1)+'" stroke="var(--red)" stroke-width="3" fill="none"/>'+gTicks+gNums
    +'<text x="200" y="96" text-anchor="middle" font-size="12" letter-spacing="5" fill="var(--ink)">GAUGE</text>'
    +'<text x="200" y="110" text-anchor="middle" font-size="6.5" letter-spacing="3" fill="var(--dim2)">SYSTEM CHRONOMETER</text>'
    +'<text x="200" y="150" text-anchor="middle" font-size="8" letter-spacing="3" fill="var(--dim2)">CPU · OVERALL %</text>'
    +sub(105,200,44,{name:'MEMORY',majors:10,redBand:[0.85,1],hand:'memHand'},'g')
    +sub(295,200,44,{name:'DISK',majors:10,redBand:[0,0.15],hand:'diskHand'},'g')
    +sub(200,295,44,{name:'BATTERY',majors:10,redBand:[0,0.12],hand:'battHand',bolt:true},'g')
    +'<g class="cpuMain" filter="url(#hs_g)" transform="rotate('+aF(0)+' 200 200)"><polygon points="150,200 194,197.6 194,202.4" fill="var(--lume)"/><polygon points="184,200 150,199 150,201" fill="var(--lume)"/></g>'
    +'<g class="cpuPeak" transform="rotate('+aF(0)+' 200 200)"><polygon points="164,200 214,199.2 214,200.8" fill="var(--red)"/><polygon points="214,200 224,199.4 224,200.6" fill="var(--red)"/></g>'
    +'<circle cx="200" cy="200" r="7" fill="#d8d8d8"/><circle cx="200" cy="200" r="2.6" fill="#000"/>';
  var cTicks='';for(i=0;i<=50;i++){var f2=i/50,a2=aF(f2),q0=P(200,200,158,a2),q1=P(200,200,i%5===0?146:152,a2);
    cTicks+='<line x1="'+q0[0]+'" y1="'+q0[1]+'" x2="'+q1[0]+'" y2="'+q1[1]+'" stroke="#585858" stroke-width="'+(i%5===0?1.6:0.9)+'"/>';}
  var clockInner=cTicks
    +'<text x="200" y="96" text-anchor="middle" font-size="12" letter-spacing="5" fill="var(--ink)">GAUGE</text>'
    +'<text x="200" y="110" text-anchor="middle" font-size="6.5" letter-spacing="3" fill="var(--dim2)">CHRONOMETER</text>'
    +sub(105,200,44,{name:'24H',majors:8,hand:'h24Hand'},'c')
    +sub(295,200,44,{name:'DATE',majors:6,textId:'dateVal',big:true},'c')
    +sub(200,295,44,{name:'DAY',majors:7,textId:'dayVal'},'c')
    +'<g class="hourH"><polygon points="200,112 196,150 197.5,206 202.5,206 204,150" fill="var(--lume)"/></g>'
    +'<g class="minH"><polygon points="200,70 197,150 199,210 201,210 203,150" fill="var(--lume)"/></g>'
    +'<g class="secH"><rect x="199.4" y="66" width="1.2" height="152" fill="var(--red)"/><circle cx="200" cy="200" r="3.2" fill="var(--red)"/></g>'
    +'<circle cx="200" cy="200" r="6" fill="#d8d8d8"/><circle cx="200" cy="200" r="2.4" fill="#000"/>';
  var app=document.getElementById('app');
  app.innerHTML='<div class="brand">Gauge</div><div class="row">'
    +'<div class="col"><div class="watch" id="w-gauge"></div><div class="cap">System</div><div class="dig" id="dg">--</div></div>'
    +'<div class="col"><div class="watch" id="w-clock"></div><div class="cap">Time</div><div class="dig" id="dt">--</div></div></div>';
  document.getElementById('w-gauge').innerHTML=shell('g',gaugeInner);
  document.getElementById('w-clock').innerHTML=shell('c',clockInner);
  var q=function(c){return document.querySelector('.'+c);};
  var memH=q('memHand'),diskH=q('diskHand'),battH=q('battHand'),cpuM=q('cpuMain'),cpuP=q('cpuPeak');
  var hourH=q('hourH'),minH=q('minH'),secH=q('secH'),h24=q('h24Hand'),dateVal=q('dateVal'),dayVal=q('dayVal');
  var DAYS=['SUN','MON','TUE','WED','THU','FRI','SAT'],MON=['JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'];
  function setSub(node,cx,cy,f){node.setAttribute('transform','rotate('+aF(clamp(f))+' '+cx+' '+cy+')');}
  function setC(node,f){node.setAttribute('transform','rotate('+aF(clamp(f))+' 200 200)');}
  function rot(node,deg){node.setAttribute('transform','rotate('+deg+' 200 200)');}
  var cpu=0,peak=0,mem=0,disk=0.5,batt=1;
  function animate(){
    if(S){
      cpu+=(S.cpu.overall-cpu)*0.22;peak+=(S.cpu.peak-peak)*0.42;mem+=(S.mem.used_frac-mem)*0.2;
      disk+=(S.disk.free_frac-disk)*0.2;batt+=(clamp(S.battery.charge)-batt)*0.2;
      setC(cpuM,cpu);setC(cpuP,peak);setSub(memH,105,200,mem);setSub(diskH,295,200,disk);setSub(battH,200,295,batt);
      document.getElementById('dg').innerHTML='CPU <b>'+Math.round(cpu*100)+'%</b> · MEM <b>'+(mem*S.mem.total_gb).toFixed(1)+'GB</b> · DISK <b>'+Math.round(disk*100)+'%</b> · BATT <b>'+Math.round(batt*100)+'%</b>';
    }
    var n=new Date();var s=n.getSeconds()+n.getMilliseconds()/1000,mm=n.getMinutes()+s/60,hh=(n.getHours()%12)+mm/60;
    rot(hourH,hh/12*360);rot(minH,mm/60*360);rot(secH,s/60*360);
    setSub(h24,105,200,(n.getHours()+mm/60)/24);dateVal.textContent=n.getDate();dayVal.textContent=DAYS[n.getDay()];
    var p2=function(x){return (x<10?'0':'')+x;};
    document.getElementById('dt').innerHTML='<b>'+p2(n.getHours())+':'+p2(n.getMinutes())+':'+p2(n.getSeconds())+'</b> · '+DAYS[n.getDay()]+' '+p2(n.getDate())+' '+MON[n.getMonth()];
    requestAnimationFrame(animate);
  }
  requestAnimationFrame(animate);
}
})();
