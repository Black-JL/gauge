// Gauge — live system dials for Übersicht (CPU / memory / disk / battery).
// Each dial shows its own reading inset at the bottom. Needles ease via CSS.

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

// static face markup (everything except the moving needle, hub, and readout)
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
      + `<text x="150" y="171" text-anchor="middle" font-size="7.5" letter-spacing="2" fill="#565656">PEAK CORE</text>` : "";
  const battOutline = cfg.battery
    ? `<g transform="translate(150 168)">`
      + `<text x="0" y="-10" text-anchor="middle" font-size="7" letter-spacing="1.6" fill="#8c8c8c">BATTERY</text>`
      + `<rect x="-13" y="-6" width="24" height="12" rx="2.4" fill="none" stroke="#8c8c8c" stroke-width="1.1"/>`
      + `<rect x="11" y="-2.6" width="2.4" height="5.2" rx="1" fill="#8c8c8c"/></g>` : "";
  return `<circle cx="150" cy="150" r="147" fill="none" stroke="#2a2a2a" stroke-width="1"/>`
    + `<circle cx="150" cy="150" r="143" fill="none" stroke="#161616" stroke-width="1.5"/>`
    + `<circle cx="150" cy="150" r="140" fill="#080808"/>`
    + red + ticks + nums + innerTrack + battOutline
    + `<text x="150" y="116" text-anchor="middle" font-size="11" letter-spacing="4" fill="#8c8c8c">${cfg.faceName}</text>`;
}

const CPU = { faceName: "CPU", redBand: [0.85, 1], minor: 50, inner: true,
  majors: [0,1,2,3,4,5,6,7,8,9,10].map((n) => ({ f: n / 10, label: String(n) })) };
const MEM = { faceName: "MEM", redBand: [0.85, 1], minor: 50,
  majors: [0,20,40,60,80,100].map((n) => ({ f: n / 100, label: String(n) })) };
const DISK = { faceName: "DISK", redBand: [0, 0.15], minor: 40, battery: true,
  majors: [{ f: 0, label: "0" }, { f: 0.5, label: "50" }, { f: 1, label: "100" }] };
const CPU_FACE = face(CPU), MEM_FACE = face(MEM), DISK_FACE = face(DISK);

const needleStyle = (deg) => ({
  transformBox: "view-box", transformOrigin: "150px 150px",
  transform: `rotate(${deg}deg)`, transition: "transform 0.28s ease-out",
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
            <g transform="translate(150 168)">
              <rect x={-10.5} y={-3.6} width={19 * clamp(batt.charge)} height={7.2} rx={1}
                    fill={batt.charge < 0.15 ? "#ff3b30" : "#32d74b"} />
              {batt.charging && (
                <path d="M 1.3 -4.5 L -2.7 0.4 L 0 0.4 L -1.3 4.5 L 3.2 -0.9 L 0.4 -0.9 Z" fill="#04270f" />
              )}
            </g>
          )}
          <g style={needleStyle(angleFor(f))}>
            <polygon points="150,150 124,148.8 124,151.2" fill="#3a3a3a" />
            <polygon points="256,150 166,149 166,151" fill="#fff" />
            <polygon points="256,150 238,149.7 238,150.3" fill="#ff3b30" />
          </g>
          <circle cx="150" cy="150" r="6.5" fill="#e8e8e8" />
          <circle cx="150" cy="150" r="2.4" fill="#000" />
          <text x="150" y="228" textAnchor="middle" fontSize="30" fontWeight="300"
                fill="#fff" style={{ fontVariantNumeric: "tabular-nums" }}>
            {val}<tspan fontSize="15" fill="#8c8c8c" dx="2">{unit}</tspan>
          </text>
          <text x="150" y="248" textAnchor="middle" fontSize="12" fill="#6a6a6a"
                letterSpacing="1.2">{sub}</text>
        </svg>
      </div>
    </div>
  );
}

export const render = ({ output }) => {
  let s = null;
  try { s = JSON.parse(output); } catch (e) { s = null; }
  if (!s || !s.cpu) return <div className="loading">Gauge starting…</div>;

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
    </div>
  );
};

export const className = `
  top: 60px; left: 60px;
  font-family: 'Helvetica Neue', Inter, system-ui, sans-serif;
  color: #fff; -webkit-font-smoothing: antialiased;
  .card { background: rgba(9,9,11,0.55); -webkit-backdrop-filter: blur(26px);
    backdrop-filter: blur(26px); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 24px; padding: 20px 26px 16px; box-shadow: 0 24px 60px rgba(0,0,0,.55); }
  .brand { letter-spacing: .52em; font-size: 10px; color: #8c8c8c; text-transform: uppercase;
    text-align: center; margin-bottom: 8px; padding-left: .52em; }
  .cluster { display: flex; align-items: center; justify-content: center; gap: 12px; }
  .gauge { display: flex; flex-direction: column; align-items: center; }
  .gauge.side .dial { width: 150px; height: 150px; }
  .gauge.center .dial { width: 208px; height: 208px; }
  .gauge.side { transform: translateY(18px); }
  .dial svg { display: block; width: 100%; height: 100%; }
  .loading { padding: 46px 60px; color: #565656; font-size: 12px; letter-spacing: .1em; }
`;
