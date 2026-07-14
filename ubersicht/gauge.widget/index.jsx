// Gauge — live system dials for Übersicht (CPU / memory / disk / battery / net).
// Reuses the minimal design. Needles ease via CSS transitions on each refresh.

export const command =
  `/usr/bin/python3 "$HOME/Library/Application Support/Übersicht/widgets/gauge.widget/gauge_stats.py"`;
export const refreshFrequency = 1000;

// ── geometry ────────────────────────────────────────────────────────────────
const START = 135, SWEEP = 270;
const d2r = (d) => (d * Math.PI) / 180;
const polar = (r, d) => [150 + r * Math.cos(d2r(d)), 150 + r * Math.sin(d2r(d))];
const angleFor = (f) => START + Math.max(0, Math.min(1, f)) * SWEEP;
const clamp = (f) => Math.max(0, Math.min(1, f));
function arcPath(r, f0, f1) {
  const a0 = angleFor(f0), a1 = angleFor(f1);
  const [x0, y0] = polar(r, a0), [x1, y1] = polar(r, a1);
  return `M ${x0} ${y0} A ${r} ${r} 0 ${a1 - a0 > 180 ? 1 : 0} 1 ${x1} ${y1}`;
}

// static face markup (everything except the moving needle + hub)
function face(cfg) {
  let ticks = "", nums = "";
  for (let i = 0; i <= cfg.minor; i++) {
    const a = angleFor(i / cfg.minor), p0 = polar(122, a), p1 = polar(116, a);
    ticks += `<line x1="${p0[0]}" y1="${p0[1]}" x2="${p1[0]}" y2="${p1[1]}" stroke="#3a3a3a" stroke-width="1"/>`;
  }
  cfg.majors.forEach((m) => {
    const a = angleFor(m.f);
    const red = cfg.redBand && m.f >= cfg.redBand[0] - 1e-6 && m.f <= cfg.redBand[1] + 1e-6;
    const col = red ? "#ff3b30" : "#fff";
    const p0 = polar(123, a), p1 = polar(107, a), tp = polar(90, a);
    ticks += `<line x1="${p0[0]}" y1="${p0[1]}" x2="${p1[0]}" y2="${p1[1]}" stroke="${col}" stroke-width="1.6" stroke-linecap="round"/>`;
    nums += `<text x="${tp[0]}" y="${tp[1] + 5}" text-anchor="middle" font-size="15" font-weight="300" fill="${col}">${m.label}</text>`;
  });
  const red = cfg.redBand
    ? `<path d="${arcPath(124, cfg.redBand[0], cfg.redBand[1])}" stroke="#ff3b30" stroke-width="4" fill="none"/>` : "";
  const innerTrack = cfg.inner
    ? `<path d="${arcPath(76, 0, 1)}" stroke="#191919" stroke-width="3.5" fill="none" stroke-linecap="round"/>`
      + `<text x="150" y="176" text-anchor="middle" font-size="7.5" letter-spacing="2" fill="#565656">PEAK CORE</text>` : "";
  const battOutline = cfg.battery
    ? `<g transform="translate(150 176)">`
      + `<text x="0" y="-11" text-anchor="middle" font-size="7" letter-spacing="1.8" fill="#8c8c8c">BATTERY</text>`
      + `<rect x="-14" y="-6.5" width="26" height="13" rx="2.5" fill="none" stroke="#8c8c8c" stroke-width="1.2"/>`
      + `<rect x="12" y="-3" width="2.6" height="6" rx="1" fill="#8c8c8c"/></g>` : "";
  return `<circle cx="150" cy="150" r="147" fill="none" stroke="#2a2a2a" stroke-width="1"/>`
    + `<circle cx="150" cy="150" r="143" fill="none" stroke="#161616" stroke-width="1.5"/>`
    + `<circle cx="150" cy="150" r="140" fill="#080808"/>`
    + red + ticks + nums + innerTrack + battOutline
    + `<text x="150" y="120" text-anchor="middle" font-size="11" letter-spacing="4" fill="#8c8c8c">${cfg.faceName}</text>`
    + `<text x="150" y="210" text-anchor="middle" font-size="8.5" letter-spacing="2.5" fill="#565656">${cfg.faceUnit}</text>`;
}

const CPU = { faceName: "CPU", faceUnit: "× 10 %  OVERALL", redBand: [0.85, 1], minor: 50, inner: true,
  majors: [0,1,2,3,4,5,6,7,8,9,10].map((n) => ({ f: n / 10, label: String(n) })) };
const MEM = { faceName: "MEM", faceUnit: "% USED", redBand: [0.85, 1], minor: 50,
  majors: [0,20,40,60,80,100].map((n) => ({ f: n / 100, label: String(n) })) };
const DISK = { faceName: "DISK", faceUnit: "% FREE", redBand: [0, 0.15], minor: 40, battery: true,
  majors: [{ f: 0, label: "0" }, { f: 0.5, label: "50" }, { f: 1, label: "100" }] };
const CPU_FACE = face(CPU), MEM_FACE = face(MEM), DISK_FACE = face(DISK);

const needleStyle = (deg) => ({
  transformBox: "view-box", transformOrigin: "150px 150px",
  transform: `rotate(${deg}deg)`, transition: "transform 0.9s ease-out",
});

function Dial({ faceHtml, cls, f, peak, batt, val, unit, sub }) {
  return (
    <div className={"gauge " + cls}>
      <div className="dial">
        <svg viewBox="0 0 300 300">
          <g dangerouslySetInnerHTML={{ __html: faceHtml }} />
          {peak != null && (
            <g style={needleStyle(angleFor(peak))}>
              <polygon points="216,150 150,149.1 150,150.9" fill="#ff3b30" />
            </g>
          )}
          {batt && (
            <g transform="translate(150 176)">
              <rect x={-11.5} y={-4} width={21 * clamp(batt.charge)} height={8} rx={1}
                    fill={batt.charge < 0.15 ? "#ff3b30" : "#32d74b"} />
              {batt.charging && (
                <path d="M 1.5 -5 L -3 0.5 L 0 0.5 L -1.5 5 L 3.5 -1 L 0.5 -1 Z" fill="#04270f" />
              )}
              <text x={0} y={19} textAnchor="middle" fontSize="8" fill="#8c8c8c">
                {Math.round(batt.charge * 100) + "%"}
              </text>
            </g>
          )}
          <g style={needleStyle(angleFor(f))}>
            <polygon points="150,150 124,148.8 124,151.2" fill="#3a3a3a" />
            <polygon points="256,150 166,149 166,151" fill="#fff" />
            <polygon points="256,150 238,149.7 238,150.3" fill="#ff3b30" />
          </g>
          <circle cx="150" cy="150" r="6.5" fill="#e8e8e8" />
          <circle cx="150" cy="150" r="2.4" fill="#000" />
        </svg>
      </div>
      <div className="val" style={val === "--" ? {} : {}}>
        {val}<span className="u">{unit}</span>
      </div>
      <div className="sub">{sub}</div>
    </div>
  );
}

function fmtRate(bps) {
  if (bps >= 1e6) return (bps / 1e6).toFixed(1) + " MB/s";
  if (bps >= 1e3) return (bps / 1e3).toFixed(0) + " KB/s";
  return Math.round(bps) + " B/s";
}
const barW = (bps) => Math.max(2, Math.min(100, (bps / 12.5e6) * 100)) + "%"; // vs ~100 Mbps

export const render = ({ output }) => {
  let s = null;
  try { s = JSON.parse(output); } catch (e) { s = null; }
  if (!s || !s.cpu) return <div className="loading">Gauge starting…</div>;

  const down = s.net ? s.net.down_bps : 0;
  const up = s.net ? s.net.up_bps : 0;

  return (
    <div className="card">
      <div className="brand">Gauge</div>
      <div className="cluster">
        <Dial faceHtml={MEM_FACE} cls="side" f={s.mem.used_frac}
              val={(s.mem.used_frac * s.mem.total_gb).toFixed(1)} unit="GB"
              sub={Math.round(s.mem.used_frac * 100) + "% of " + Math.round(s.mem.total_gb)} />
        <Dial faceHtml={CPU_FACE} cls="center" f={s.cpu.overall} peak={s.cpu.peak}
              val={Math.round(s.cpu.overall * 100)} unit="%"
              sub={"peak " + Math.round(s.cpu.peak * 100) + "%"} />
        <Dial faceHtml={DISK_FACE} cls="side" f={s.disk.free_frac} batt={s.battery}
              val={Math.round(s.disk.free_frac * 100)} unit="%"
              sub={Math.round(s.disk.free_frac * s.disk.total_gb) + " GB free"} />
      </div>
      <div className="net">
        <div className="netcol">
          <span className="arw dn">▼</span>
          <span className="nval">{fmtRate(down)}</span>
          <div className="bar"><div className="dnfill" style={{ width: barW(down) }} /></div>
        </div>
        <div className="netcol">
          <span className="arw up">▲</span>
          <span className="nval">{fmtRate(up)}</span>
          <div className="bar"><div className="upfill" style={{ width: barW(up) }} /></div>
        </div>
      </div>
    </div>
  );
};

export const className = `
  top: 60px; left: 60px;
  font-family: 'Helvetica Neue', Inter, system-ui, sans-serif;
  color: #fff; -webkit-font-smoothing: antialiased;
  .card { background: rgba(9,9,11,0.55); -webkit-backdrop-filter: blur(26px);
    backdrop-filter: blur(26px); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 24px; padding: 22px 28px 18px; box-shadow: 0 24px 60px rgba(0,0,0,.55); }
  .brand { letter-spacing: .52em; font-size: 10px; color: #8c8c8c; text-transform: uppercase;
    text-align: center; margin-bottom: 14px; padding-left: .52em; }
  .cluster { display: flex; align-items: center; justify-content: center; gap: 14px; }
  .gauge { display: flex; flex-direction: column; align-items: center; }
  .gauge.side .dial { width: 118px; height: 118px; }
  .gauge.center .dial { width: 172px; height: 172px; }
  .gauge.side { transform: translateY(14px); }
  .dial svg { display: block; width: 100%; height: 100%; }
  .val { margin-top: 9px; font-size: 15px; font-weight: 200; font-variant-numeric: tabular-nums; }
  .gauge.center .val { font-size: 20px; }
  .val .u { font-size: .5em; color: #8c8c8c; margin-left: .2em; letter-spacing: .1em; }
  .sub { font-size: 8px; letter-spacing: .18em; color: #565656; text-transform: uppercase; margin-top: 3px; }
  .net { margin-top: 16px; padding-top: 13px; border-top: 1px solid rgba(255,255,255,0.08);
    display: flex; justify-content: center; gap: 24px; }
  .netcol { display: flex; align-items: center; gap: 8px; width: 150px; }
  .arw { font-size: 9px; } .arw.dn { color: #32d74b; } .arw.up { color: #4d9fff; }
  .nval { font-size: 12px; font-variant-numeric: tabular-nums; min-width: 62px; color: #e8e8e8; }
  .bar { flex: 1; height: 3px; background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden; }
  .bar > div { height: 100%; border-radius: 2px; transition: width .9s ease-out; }
  .dnfill { background: #32d74b; } .upfill { background: #4d9fff; }
  .loading { padding: 46px 60px; color: #565656; font-size: 12px; letter-spacing: .1em; }
`;
