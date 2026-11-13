import React from 'react';
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { C, F } from '../kit/theme';
import { Camera, Caption, Grade, PaperTexture, Vignette } from '../kit/lens';
import { Clock, Laptop, Phone, Stamp } from '../kit/props';
import { Portrait } from '../kit/portrait';
import { LivePage } from '../kit/screen';
import { easeInOut, easeOut, fade, lerp, rand, settle, stamp } from '../kit/motion';

// ============================================================================
// ACT 3 — Night two. Warm lamp, a locked-off camera, the product at full height.
// ============================================================================

/** The warm desk every night-two shot sits on. */
const WarmDesk: React.FC<{ children?: React.ReactNode; lamp?: number }> = ({ children, lamp = 1 }) => (
  <AbsoluteFill style={{ background: '#2a2119' }}>
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 70% at 35% 20%, rgba(255,196,120,${0.55 * lamp}) 0%, rgba(60,40,24,0) 70%)` }} />
    <AbsoluteFill style={{ background: 'repeating-linear-gradient(92deg, rgba(0,0,0,0.05) 0 3px, rgba(0,0,0,0) 3px 19px)' }} />
    {children}
  </AbsoluteFill>
);

const Callout: React.FC<{ text: string; f: number; at: number; x: number; y: number; w?: number }> = ({ text, f, at, x, y, w = 360 }) => {
  const { fps } = useVideoConfig();
  const s = stamp(f, at, fps);
  return (
    <div
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width: w,
        background: C.paper,
        border: `3px solid ${C.ink}`,
        boxShadow: `7px 7px 0 ${C.ink}`,
        padding: '18px 22px 14px',
        fontFamily: F.body,
        fontWeight: 600,
        fontSize: 27,
        lineHeight: 1.2,
        color: C.ink,
        opacity: Math.min(1, s * 1.4),
        transform: `scale(${1.25 - 0.25 * s}) rotate(${(1 - s) * -3}deg)`,
      }}
    >
      {text}
    </div>
  );
};

// ---- P1. The real JEE page on a phone -------------------------------------
const PhoneHero: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = settle(f, 0, fps, 22);
  // scroll the real page: title → the six files
  const scroll = interpolate(f, [40, 120], [0, 700], { easing: easeInOut, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const dolly = lerp(f, [0, 180], [1.0, 1.06]);
  return (
    <WarmDesk>
      <Camera scale={dolly} x={lerp(f, [0, 180], [10, -10])}>
        <div style={{ position: 'absolute', left: 300, top: 70 + (1 - enter) * 300, transform: `rotate(${-3 + enter * 1}deg)` }}>
          <Phone width={500}>
            <LivePage page="jee" width={500} scroll={scroll} />
          </Phone>
        </div>
      </Camera>
      <Callout text="The exam's own rules, from its official bulletin." f={f} at={20} x={30} y={760} w={300} />
      <Callout text="Every file it asks for. Six of them, prepared." f={f} at={120} x={690} y={860} w={340} />
      <Grade tone="warm" amount={0.5} />
      <Vignette strength={0.5} />
    </WarmDesk>
  );
};

// ---- P2. Everything at once ------------------------------------------------
const FILES = [
  { label: 'selfie.jpg', kind: 'photo' },
  { label: 'sign.jpg', kind: 'sign' },
  { label: 'class10.pdf', kind: 'doc' },
  { label: 'aadhaar.jpg', kind: 'doc' },
  { label: 'pwd.pdf', kind: 'doc' },
  { label: 'cert.jpg', kind: 'doc' },
];

const FileTile: React.FC<{ kind: string; label: string; size?: number }> = ({ kind, label, size = 150 }) => (
  <div style={{ width: size, background: C.paper, border: `3px solid ${C.ink}`, boxShadow: `5px 5px 0 ${C.ink}`, padding: 8 }}>
    <div style={{ height: size * 1.05, background: kind === 'doc' ? '#efe9dc' : '#ddd', position: 'relative', overflow: 'hidden' }}>
      {kind === 'photo' ? <Portrait variant="source" width={size - 22} height={size * 1.05} /> : null}
      {kind === 'sign' ? (
        <svg width="100%" height="100%" viewBox="0 0 100 100" style={{ background: 'linear-gradient(120deg,#b8ad90,#8f8670)' }}>
          <path d="M10 60 C 20 30, 30 30, 30 55 C 30 70, 45 40, 55 50 C 65 60, 70 35, 90 45" stroke="#1c2a6a" strokeWidth="3" fill="none" />
        </svg>
      ) : null}
      {kind === 'doc'
        ? [0, 1, 2, 3, 4, 5].map((i) => <div key={i} style={{ height: 5, margin: '12px 10px 0', background: '#b9b2a2', width: `${60 + rand(i + label.length) * 30}%` }} />)
        : null}
    </div>
    <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: size * 0.11, marginTop: 6, color: C.ink, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{label}</div>
  </div>
);

const DropAll: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <WarmDesk>
      <div style={{ position: 'absolute', left: 290, top: 120 }}>
        <Phone width={500}>
          <div style={{ position: 'absolute', inset: 0, background: C.paper, padding: '80px 26px 0', fontFamily: F.body }}>
            <div style={{ fontWeight: 600, fontSize: 13, letterSpacing: '0.09em', color: C.ink55 }}>JEE (MAIN) 2027 · YOUR FILES</div>
            <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 52, lineHeight: 0.9, marginTop: 10 }}>ADD EVERYTHING.<br />WE SORT IT.</div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14, marginTop: 30 }}>
              {FILES.map((fl, i) => {
                const s = settle(f, 28 + i * 4, fps, 16);
                return (
                  <div key={fl.label} style={{ opacity: s > 0.5 ? 1 : 0, transform: `scale(${0.8 + 0.2 * s})` }}>
                    <FileTile kind={fl.kind} label={fl.label} size={128} />
                  </div>
                );
              })}
            </div>
          </div>
        </Phone>
      </div>
      {/* the same files in flight, from the edge of frame into the screen */}
      {FILES.map((fl, i) => {
        const t = lerp(f, [i * 4, 28 + i * 4], [0, 1], easeInOut);
        const sx = i % 2 ? 1100 : -260;
        const sy = 200 + i * 150;
        const tx = 330 + (i % 3) * 142;
        const ty = 420 + Math.floor(i / 3) * 190;
        const arc = Math.sin(t * Math.PI) * -160;
        return (
          <div
            key={fl.label}
            style={{
              position: 'absolute',
              left: sx + (tx - sx) * t,
              top: sy + (ty - sy) * t + arc,
              transform: `rotate(${(1 - t) * (i % 2 ? 18 : -18)}deg) scale(${1.4 - 0.5 * t})`,
              opacity: t < 0.98 ? 1 : 0,
            }}
          >
            <FileTile kind={fl.kind} label={fl.label} size={128} />
          </div>
        );
      })}
      <Caption text="Photo, signature, certificates, ID. All at once." opacity={fade(f, 30, 8)} y={1200} />
      <Grade tone="warm" amount={0.5} />
      <Vignette strength={0.5} />
    </WarmDesk>
  );
};

// ---- P3. The engine as one continuous take across a paper table ------------
const STATION = 1080;

/** Ink blooming in water: white clouds that grow, displaced by turbulence. */
const InkBloom: React.FC<{ t: number; w: number; h: number; seed?: number }> = ({ t, w, h, seed = 4 }) => {
  const blobs = [
    [0.1, 0.15, 0.0], [0.85, 0.1, 0.08], [0.15, 0.6, 0.12], [0.9, 0.55, 0.05], [0.5, 0.05, 0.18], [0.05, 0.95, 0.2], [0.95, 0.95, 0.15],
  ];
  return (
    <svg width={w} height={h} style={{ position: 'absolute', inset: 0 }}>
      <filter id={`ink${seed}`} x="-30%" y="-30%" width="160%" height="160%">
        <feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves={4} seed={seed} />
        <feDisplacementMap in="SourceGraphic" scale={70 + t * 40} xChannelSelector="R" yChannelSelector="G" />
        <feGaussianBlur stdDeviation={2} />
      </filter>
      <g filter={`url(#ink${seed})`}>
        {blobs.map(([x, y, d], i) => {
          const local = Math.max(0, Math.min(1, (t - d) / (1 - d)));
          const r = Math.pow(local, 0.7) * Math.max(w, h) * 0.7;
          return <circle key={i} cx={x * w} cy={y * h} r={r} fill="#ffffff" opacity={0.92} />;
        })}
      </g>
    </svg>
  );
};

const Gauge: React.FC<{ kb: number }> = ({ kb }) => {
  const max = 200;
  const a = -120 + (Math.min(kb, max * 1.04) / max) * 240;
  return (
    <svg width={560} height={420} viewBox="-150 -140 300 200">
      <path d="M -120 0 A 120 120 0 1 1 120 0" fill="none" stroke={C.ink} strokeWidth={3} transform="rotate(0)" />
      {Array.from({ length: 21 }, (_, i) => {
        const ang = -120 + i * 12;
        const long = i % 5 === 0;
        return <line key={i} x1={0} y1={-108} x2={0} y2={long ? -92 : -100} stroke={C.ink} strokeWidth={long ? 3 : 1.4} transform={`rotate(${ang})`} />;
      })}
      {[0, 50, 100, 150, 200].map((v, i) => {
        const ang = ((-120 + i * 60) * Math.PI) / 180;
        return (
          <text key={v} x={Math.sin(ang) * 76} y={-Math.cos(ang) * 76 + 5} textAnchor="middle" fontFamily={F.display} fontWeight={900} fontSize={16} fill={C.ink}>
            {v}
          </text>
        );
      })}
      <path d="M 105 -62 A 120 120 0 0 1 120 0" fill="none" stroke={C.signal} strokeWidth={8} transform="rotate(-1)" />
      <line x1={0} y1={14} x2={0} y2={-112} stroke={C.signal} strokeWidth={3.5} transform={`rotate(${a})`} />
      <circle r={9} fill={C.ink} />
    </svg>
  );
};

const EngineTable: React.FC = () => {
  const f = useCurrentFrame();
  // station timings (local frames). The camera holds, then glides to the next station.
  const moves: [number, number][] = [[100, 122], [200, 216], [262, 276], [322, 336]];
  const camX = moves.reduce((acc, [a, b]) => acc + lerp(f, [a, b], [0, 1], easeInOut) * STATION, 0);
  const s0 = f; // portrait station
  const coverage = Math.round(interpolate(s0, [20, 50], [41, 80], { easing: easeOut, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }));
  const trace = lerp(s0, [8, 40], [0, 1], easeOut);
  const frame = lerp(s0, [50, 62], [0, 1], easeOut);
  const bloom = lerp(s0, [62, 100], [0, 1], easeInOut);
  const kb = interpolate(f - 120, [0, 50], [3400, 187], { easing: easeOut, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const name = 'jee-main_photo.jpg';
  const typed = name.slice(0, Math.max(0, Math.floor((f - 220) / 1.6)));
  const signClean = lerp(f, [280, 310], [0, 1], easeInOut);
  const pdfT = lerp(f, [340, 380], [0, 1], easeInOut);
  const caps: [number, number, string][] = [
    [10, 60, 'Head found. Face coverage measured.'],
    [62, 100, 'Background turned exam-white.'],
    [125, 200, 'Just under the limit. Still sharp.'],
    [215, 262, 'Named the way the portal wants.'],
    [275, 322, 'Signature cleaned, shadow gone.'],
    [335, 420, 'Certificates merged, rotated, sized.'],
  ];
  const cap = caps.find(([a, b]) => f >= a && f < b);
  return (
    <AbsoluteFill style={{ background: '#e9e3d6', overflow: 'hidden' }}>
      <PaperTexture opacity={0.55} seed={9} />
      <AbsoluteFill style={{ transform: `translateX(${-camX}px)` }}>
        {/* Station 1: the photograph */}
        <div style={{ position: 'absolute', left: 0, top: 0, width: STATION, height: 1350 }}>
          <div style={{ position: 'absolute', left: 190, top: 150, width: 700, height: 900, background: C.paper, boxShadow: '0 30px 60px rgba(60,40,20,0.3)', padding: 30 }}>
            <div style={{ position: 'relative', width: 640, height: 820 }}>
              <Portrait variant="source" width={640} height={820} whiten={bloom} />
              {/* the ink, soft-masked away from her so she is never haloed */}
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  opacity: 1 - interpolate(bloom, [0.85, 1], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }),
                  maskImage: 'radial-gradient(ellipse 36% 52% at 50% 62%, transparent 62%, #000 82%)',
                  WebkitMaskImage: 'radial-gradient(ellipse 36% 52% at 50% 62%, transparent 62%, #000 82%)',
                }}
              >
                <InkBloom t={bloom} w={640} h={820} />
              </div>
              <div style={{ position: 'absolute', inset: 0, opacity: interpolate(bloom, [0.75, 1], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }}>
                <Portrait variant="prepared" width={640} height={820} />
              </div>
              {/* the ink line tracing the head */}
              <svg width={640} height={820} style={{ position: 'absolute', inset: 0 }}>
                <ellipse cx={320} cy={420} rx={190} ry={260} fill="none" stroke={C.signal} strokeWidth={5} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - trace} opacity={1 - bloom} />
              </svg>
              {/* the exam frame snapping to 413 × 531 */}
              <div style={{ position: 'absolute', left: 320 - (1 - frame) * 40 - 300, top: 30 - (1 - frame) * 30, width: 600 + (1 - frame) * 80, height: 772 + (1 - frame) * 60, border: `4px solid ${C.ink}`, opacity: frame * (1 - bloom * 0.6) }} />
            </div>
          </div>
          <div style={{ position: 'absolute', left: 190, top: 1080, display: 'flex', gap: 18, alignItems: 'center' }}>
            <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 84, color: C.ink, lineHeight: 0.8 }}>{coverage}%</div>
            <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 24, color: C.ink70, lineHeight: 1.1 }}>face<br />coverage</div>
            <div style={{ marginLeft: 30, fontFamily: F.display, fontWeight: 900, fontSize: 52, color: C.ink, opacity: frame }}>413 × 531 PX</div>
          </div>
        </div>
        {/* Station 2: the size dial */}
        <div style={{ position: 'absolute', left: STATION, top: 0, width: STATION, height: 1350, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: C.paper, border: `3px solid ${C.ink}`, boxShadow: `9px 9px 0 ${C.ink}`, padding: '40px 40px 30px' }}>
            <Gauge kb={kb} />
            <div style={{ textAlign: 'center', fontFamily: F.display, fontWeight: 900, fontSize: 120, lineHeight: 0.85, color: C.ink }}>
              {Math.round(kb)} <span style={{ fontSize: 60 }}>KB</span>
            </div>
            <div style={{ textAlign: 'center', fontFamily: F.body, fontWeight: 600, fontSize: 28, color: C.ink55, marginTop: 8 }}>limit 200 KB · JPEG</div>
          </div>
        </div>
        {/* Station 3: the filename, typed */}
        <div style={{ position: 'absolute', left: STATION * 2, top: 0, width: STATION, height: 1350, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: '#fbf7ee', padding: '70px 60px', width: 860, boxShadow: '0 20px 50px rgba(60,40,20,0.25)', transform: 'rotate(-1.5deg)' }}>
            <div style={{ fontFamily: F.type, fontSize: 64, color: '#1a1a1a', letterSpacing: '0.01em' }}>
              {typed}
              <span style={{ opacity: Math.floor(f / 6) % 2 ? 1 : 0, color: C.signal }}>_</span>
            </div>
          </div>
        </div>
        {/* Station 4: the signature */}
        <div style={{ position: 'absolute', left: STATION * 3, top: 0, width: STATION, height: 1350, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ position: 'relative', width: 860, height: 420, boxShadow: '0 20px 50px rgba(60,40,20,0.25)' }}>
            <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(115deg,#b9ad8c 0%,#d8cfb4 45%,#8e8670 100%)' }} />
            <div style={{ position: 'absolute', inset: 0, background: '#ffffff', clipPath: `inset(0 ${(1 - signClean) * 100}% 0 0)` }} />
            <svg width="860" height="420" viewBox="0 0 860 420" style={{ position: 'absolute' }}>
              <path
                d="M140 260 C 180 140, 230 140, 220 240 C 214 300, 260 190, 300 200 C 340 210, 320 270, 360 240 C 400 210, 420 160, 450 230 C 470 280, 520 180, 560 210 C 600 240, 640 200, 700 190"
                stroke={signClean > 0.5 ? '#0d1a5c' : '#1c2a6a'}
                strokeWidth={signClean > 0.5 ? 6 : 5}
                fill="none"
                strokeLinecap="round"
                opacity={0.75 + signClean * 0.25}
              />
            </svg>
            <div style={{ position: 'absolute', left: `${signClean * 100}%`, top: -20, bottom: -20, width: 4, background: C.signal, opacity: signClean > 0 && signClean < 1 ? 1 : 0 }} />
          </div>
        </div>
        {/* Station 5: the certificates */}
        <div style={{ position: 'absolute', left: STATION * 4, top: 0, width: STATION, height: 1350 }}>
          {[0, 1, 2, 3].map((i) => {
            const startX = 120 + i * 220;
            const startR = [8, -95, -4, 12][i];
            const endX = 330;
            const x = startX + (endX - startX) * pdfT + i * 14 * pdfT;
            const y = 360 + (i % 2) * 120 * (1 - pdfT) + i * 14 * pdfT;
            const r = startR * (1 - pdfT);
            return (
              <div key={i} style={{ position: 'absolute', left: x, top: y, width: 400, height: 540, background: '#fbf8f0', border: `3px solid ${C.ink}`, boxShadow: `6px 6px 0 ${C.ink}`, transform: `rotate(${r}deg)`, padding: 34 }}>
                <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 30, color: C.ink }}>{['CLASS X', 'ID PROOF', 'PWD CERT.', 'CATEGORY'][i]}</div>
                {[0, 1, 2, 3, 4, 5, 6].map((k) => <div key={k} style={{ height: 8, background: '#cfc8b8', marginTop: 22, width: `${55 + rand(k + i * 7) * 40}%` }} />)}
              </div>
            );
          })}
          <div style={{ position: 'absolute', left: 300, top: 1020, fontFamily: F.display, fontWeight: 900, fontSize: 56, color: C.ink, opacity: fade(f, 375, 8) }}>
            ONE PDF · 4 PAGES · 286 KB
          </div>
        </div>
      </AbsoluteFill>
      {cap ? <Caption text={cap[2]} tone="dark" y={70} size={44} opacity={fade(f, cap[0], 6, cap[1] - 6, 6)} /> : null}
      <Grade tone="warm" amount={0.4} />
      <Vignette strength={0.35} />
    </AbsoluteFill>
  );
};

// ---- P4. Before and after, on the phone -----------------------------------
const BeforeAfter: React.FC = () => {
  const f = useCurrentFrame();
  const pos = interpolate(f, [15, 55, 75, 100], [0.92, 0.12, 0.12, 0.5], { easing: easeInOut, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const w = 500;
  return (
    <WarmDesk>
      <div style={{ position: 'absolute', left: 290, top: 110 }}>
        <Phone width={w}>
          <div style={{ position: 'absolute', inset: 0, background: C.paper, padding: '76px 22px 0', fontFamily: F.body }}>
            <div style={{ fontWeight: 600, fontSize: 13, letterSpacing: '0.09em', color: C.ink55 }}>PHOTOGRAPH · READY</div>
            <div style={{ position: 'relative', marginTop: 14, width: w - 44, height: (w - 44) * 1.286, border: `3px solid ${C.ink}`, overflow: 'hidden' }}>
              <Portrait variant="source" width={w - 50} height={(w - 50) * 1.286} />
              <div style={{ position: 'absolute', inset: 0, clipPath: `inset(0 0 0 ${pos * 100}%)` }}>
                <Portrait variant="prepared" width={w - 50} height={(w - 50) * 1.286} />
              </div>
              <div style={{ position: 'absolute', top: 0, bottom: 0, left: `${pos * 100}%`, width: 4, marginLeft: -2, background: C.ink }}>
                <div style={{ position: 'absolute', top: '50%', left: -22, width: 44, height: 44, marginTop: -22, background: C.signal, border: `3px solid ${C.ink}` }} />
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 14, fontWeight: 700, fontSize: 18 }}>
              <span>413 × 531 px</span><span>187 KB</span><span>JPEG</span>
            </div>
            <div style={{ marginTop: 14, padding: '10px 14px', background: C.okFill, border: `2px solid ${C.okLine}`, color: C.okLine, fontWeight: 700, fontSize: 18 }}>
              ✓ Meets every JEE (Main) photo rule we check
            </div>
          </div>
        </Phone>
      </div>
      {/* the touch point */}
      <div style={{ position: 'absolute', left: 290 + 18 + 22 + pos * (w - 44) - 36, top: 110 + 18 + 76 + 14 + ((w - 44) * 1.286) / 2 - 36, width: 72, height: 72, borderRadius: 999, border: `4px solid ${C.paper}`, background: 'rgba(17,17,16,0.25)', boxShadow: '0 0 0 3px rgba(17,17,16,0.5)', opacity: f > 10 && f < 105 ? 1 : 0 }} />
      <Caption text="Drag to compare. Nothing about you is changed." opacity={fade(f, 20, 8)} y={1210} />
      <Grade tone="warm" amount={0.5} />
      <Vignette strength={0.5} />
    </WarmDesk>
  );
};

// ---- P5. The kit, sealed; and the same kit on a laptop ----------------------
const Kit: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const files = ['jee-main_photo.jpg', 'jee-main_signature.jpg', 'jee-main_class-x.pdf', 'jee-main_id-proof.jpg', 'jee-main_pwd.pdf', 'jee-main_physical.pdf'];
  const seal = stamp(f, 62, fps);
  return (
    <AbsoluteFill style={{ background: '#e9e3d6' }}>
      <PaperTexture opacity={0.5} seed={12} />
      {/* kraft envelope */}
      <div style={{ position: 'absolute', left: 140, top: 520, width: 800, height: 560, background: '#c9a46a', boxShadow: '0 30px 60px rgba(60,40,20,0.35)' }}>
        <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(150deg, rgba(255,255,255,0.12), rgba(0,0,0,0.1))' }} />
        <svg width="800" height="560" style={{ position: 'absolute' }}><path d="M0 0 L400 300 L800 0" fill="none" stroke="rgba(80,55,20,0.45)" strokeWidth={3} /></svg>
        <div style={{ position: 'absolute', left: 120, top: 330, opacity: Math.min(1, seal * 1.3), transform: `scale(${1.6 - 0.6 * seal})`, transformOrigin: 'left center' }}>
          <Stamp text="JEE (MAIN) 2027 · COMPLETE KIT" size={46} color={C.ink} rotate={-3} />
        </div>
      </div>
      {/* the files dropping in */}
      {files.map((name, i) => {
        const t = lerp(f, [i * 7, i * 7 + 22], [0, 1], easeInOut);
        return (
          <div key={name} style={{ position: 'absolute', left: 200 + i * 18, top: 120 + i * 62 + t * (520 - 120 - i * 62 + 60), opacity: t < 1 ? 1 : 0, width: 680, padding: '18px 22px', background: C.paper, border: `3px solid ${C.ink}`, boxShadow: `6px 6px 0 ${C.ink}`, fontFamily: F.body, fontWeight: 700, fontSize: 28, display: 'flex', justifyContent: 'space-between', transform: `rotate(${(i % 2 ? 1 : -1) * 2}deg)` }}>
            <span>{name}</span><span style={{ color: C.okLine }}>✓</span>
          </div>
        );
      })}
      <Caption text="One kit. Every file, ready to upload." tone="dark" y={1180} opacity={fade(f, 70, 8)} />
      <Grade tone="warm" amount={0.35} />
      <Vignette strength={0.35} />
    </AbsoluteFill>
  );
};

const Devices: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = settle(f, 0, fps, 22);
  const p = settle(f, 10, fps, 20);
  return (
    <WarmDesk>
      <Camera scale={lerp(f, [0, 90], [1.04, 1.0])}>
        <div style={{ position: 'absolute', left: 40, top: 300, opacity: s, transform: `translateY(${(1 - s) * 60}px)` }}>
          <Laptop width={760} src="ui/d-jee.png" />
        </div>
        <div style={{ position: 'absolute', left: 600, top: 470 + (1 - p) * 300, transform: 'rotate(4deg)' }}>
          <Phone width={340}>
            <LivePage page="jee" width={340} scroll={0} />
          </Phone>
        </div>
      </Camera>
      <Caption text="Feels like an app on your phone. Works on a laptop too." opacity={fade(f, 14, 8)} y={110} />
      <Grade tone="warm" amount={0.5} />
      <Vignette strength={0.5} />
    </WarmDesk>
  );
};

// ---- P6. The stamps --------------------------------------------------------
const STAMPS: { t: string; c: string; x: number; y: number; r: number; size: number }[] = [
  { t: 'FREE', c: C.signal, x: 90, y: 150, r: -6, size: 120 },
  { t: 'NO LOGIN', c: C.ink, x: 560, y: 220, r: 4, size: 76 },
  { t: '770+ EXAMS', c: C.ink, x: 110, y: 430, r: 3, size: 86 },
  { t: 'DEADLINES TRACKED', c: C.okLine, x: 200, y: 640, r: -3, size: 72 },
  { t: 'हिंदी में भी', c: C.signal, x: 110, y: 840, r: -5, size: 76 },
  { t: 'FILES ERASED AUTOMATICALLY', c: C.ink, x: 70, y: 1070, r: 2, size: 58 },
];

const Stamps: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: C.paper }}>
      <PaperTexture opacity={0.45} seed={21} />
      {STAMPS.map((s, i) => {
        const at = 6 + i * 14;
        const v = stamp(f, at, fps);
        const isHindi = s.t.startsWith('हिं');
        return (
          <div key={s.t} style={{ position: 'absolute', left: s.x, top: s.y, opacity: f >= at ? 1 : 0, transform: `scale(${1.5 - 0.5 * v})`, transformOrigin: 'left center' }}>
            <div style={isHindi ? { fontFamily: F.hindi } : undefined}>
              {isHindi ? (
                <div style={{ display: 'inline-block', border: `6px solid ${s.c}`, color: s.c, fontFamily: F.hindi, fontWeight: 700, fontSize: s.size, padding: '10px 26px 0', transform: `rotate(${s.r}deg)` }}>{s.t}</div>
              ) : (
                <Stamp text={s.t} color={s.c} size={s.size} rotate={s.r} />
              )}
            </div>
          </div>
        );
      })}
      {/* the camera feels each hit */}
      <AbsoluteFill style={{ background: C.ink, opacity: STAMPS.some((_, i) => f - (6 + i * 14) >= 0 && f - (6 + i * 14) < 2) ? 0.04 : 0 }} />
    </AbsoluteFill>
  );
};

// ---- P7. 11:19 ------------------------------------------------------------
const FiveMinutes: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <WarmDesk>
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
        <Camera scale={lerp(f, [0, 90], [1.0, 1.05])}>
          <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
            <Clock minutes={23 * 60 + 19} size={600} face="#efe7d6" />
          </AbsoluteFill>
        </Camera>
      </AbsoluteFill>
      <div style={{ position: 'absolute', left: 0, right: 0, top: 1060, textAlign: 'center', opacity: fade(f, 12, 8) }}>
        <span style={{ fontFamily: F.display, fontWeight: 900, fontSize: 120, color: C.ink, background: C.signal, padding: '14px 26px 0', lineHeight: 0.84 }}>11:19 PM.</span>
      </div>
      <Caption text="Five minutes." opacity={fade(f, 40, 8)} y={1220} size={52} />
      <Grade tone="warm" amount={0.6} />
      <Vignette strength={0.6} />
    </WarmDesk>
  );
};

export const ACT3 = 1200;
export const Act3: React.FC = () => (
  <AbsoluteFill>
    <Sequence durationInFrames={180}><PhoneHero /></Sequence>
    <Sequence from={180} durationInFrames={90}><DropAll /></Sequence>
    <Sequence from={270} durationInFrames={420}><EngineTable /></Sequence>
    <Sequence from={690} durationInFrames={120}><BeforeAfter /></Sequence>
    <Sequence from={810} durationInFrames={90}><Kit /></Sequence>
    <Sequence from={900} durationInFrames={90}><Devices /></Sequence>
    <Sequence from={990} durationInFrames={120}><Stamps /></Sequence>
    <Sequence from={1110} durationInFrames={90}><FiveMinutes /></Sequence>
  </AbsoluteFill>
);
