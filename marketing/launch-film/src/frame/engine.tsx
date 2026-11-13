import React from 'react';
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { C, F } from '../kit/theme';
import { easeIn, easeInOut, easeOut, fade, lerp } from '../kit/motion';
import { Beam, Dust, Flare, HIT, Rect, Slam, Studio, mixRect, shake } from './cinema';
import data from '../../public/photo/landmarks.json';

// ============================================================================
// THE ENGINE — one continuous shot. Every overlay is the real engine's data for this photo:
// landmarks, head box, crop window, matte outline, final size and bytes.
// ============================================================================

const E = HIT.engine; // 630 690 735 780 825 870 900 930 975 1020
const SW = 1086;
const SH = 1448;
const crop = data.crop as { left: number; top: number; right: number; bottom: number };
const head = data.head as { left: number; top: number; right: number; bottom: number };
const KB = Math.round((data.final.bytes as number) / 1024);
// the engine's own measurements for this photograph
const COVER_END = Math.round(((data as { head_height_ratio?: number }).head_height_ratio ?? 0.8) * 100);
const COVER_START = Math.round(((data.head.bottom as number) - (data.head.top as number)) / 1448 * 100);

// the print at rest, and the screen-space mapping of source pixels
export const PRINT: Rect = { x: 190, y: 150, w: 700, h: 700 * (SH / SW) };
const k = PRINT.w / SW;
const X = (x: number) => PRINT.x + x * k;
const Y = (y: number) => PRINT.y + y * k;
const CROP: Rect = { x: X(crop.left), y: Y(crop.top), w: (crop.right - crop.left) * k, h: (crop.bottom - crop.top) * k };
const FULL: Rect = { x: PRINT.x, y: PRINT.y, w: PRINT.w, h: PRINT.h };
// where the camera ends: the finished photograph, large and centred above the checks
// sized from the crop, so the finished photograph always lands 480 px wide
const HERO_W = 480;
const HERO_SCALE = HERO_W / CROP.w;
const HERO_C = { x: 540, y: 560 };
export const PHOTO_END: Rect = {
  x: HERO_C.x - (CROP.w * HERO_SCALE) / 2,
  y: HERO_C.y - (CROP.h * HERO_SCALE) / 2,
  w: CROP.w * HERO_SCALE,
  h: CROP.h * HERO_SCALE,
};

/** The matte outline as a smooth path (Catmull-Rom through the engine's contour). */
const contourPath = (() => {
  const p = (data.contour as number[][]).map(([x, y]) => [X(x), Y(y)]);
  let d = `M ${p[0][0]} ${p[0][1]}`;
  for (let i = 0; i < p.length; i++) {
    const p0 = p[(i - 1 + p.length) % p.length], p1 = p[i], p2 = p[(i + 1) % p.length], p3 = p[(i + 2) % p.length];
    d += ` C ${p1[0] + (p2[0] - p0[0]) / 6} ${p1[1] + (p2[1] - p0[1]) / 6}, ${p2[0] - (p3[0] - p1[0]) / 6} ${p2[1] - (p3[1] - p1[1]) / 6}, ${p2[0]} ${p2[1]}`;
  }
  return d;
})();

const POINTS = Object.values(data.points as Record<string, number[]>).map(([x, y]) => [X(x), Y(y)]);

const Step: React.FC<{ n: string; t: string; f: number; at: number; until: number }> = ({ n, t, f, at, until }) => (
  <div style={{ position: 'absolute', left: 64, top: 70, display: 'flex', gap: 16, alignItems: 'baseline', opacity: fade(f, at, 5, until - 5, 5), transform: `translateX(${(1 - lerp(f, [at, at + 6], [0, 1], easeOut)) * -30}px)` }}>
    <span style={{ fontFamily: F.body, fontWeight: 700, fontSize: 26, color: C.signal, letterSpacing: '0.12em' }}>{n}</span>
    <Slam font={F.display} size={64} color={C.paper}>{t}</Slam>
  </div>
);

const Readout: React.FC<{ label: string; value: string; f: number; at: number; good?: boolean; x?: number; y?: number; size?: number }> = ({ label, value, f, at, good, x = 64, y = 1110, size = 120 }) => (
  <div style={{ position: 'absolute', left: x, top: y, opacity: fade(f, at, 5) }}>
    <div style={{ fontFamily: F.body, fontWeight: 700, fontSize: 22, letterSpacing: '0.14em', color: '#9b948a' }}>{label}</div>
    <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: size, lineHeight: 0.85, color: good ? C.paper : C.paper, marginTop: 6 }}>
      {value}
      {good ? <span style={{ color: '#5fd38d' }}> ✓</span> : null}
    </div>
  </div>
);

const Brackets: React.FC<{ r: Rect; color: string; len?: number; w?: number; o?: number }> = ({ r, color, len = 40, w = 5, o = 1 }) => {
  const s: React.CSSProperties = { position: 'absolute', width: len, height: len, borderColor: color, borderStyle: 'solid', borderWidth: 0 };
  return (
    <div style={{ position: 'absolute', left: r.x, top: r.y, width: r.w, height: r.h, opacity: o }}>
      <div style={{ ...s, left: -w, top: -w, borderLeftWidth: w, borderTopWidth: w }} />
      <div style={{ ...s, right: -w, top: -w, borderRightWidth: w, borderTopWidth: w }} />
      <div style={{ ...s, left: -w, bottom: -w, borderLeftWidth: w, borderBottomWidth: w }} />
      <div style={{ ...s, right: -w, bottom: -w, borderRightWidth: w, borderBottomWidth: w }} />
    </div>
  );
};

export const Engine: React.FC = () => {
  const f = useCurrentFrame();
  const sh = shake(f, 10);

  // the arrival from the dive: the print starts filling the frame and pulls back to rest
  const arrive = lerp(f, [E[0], E[0] + 22], [0, 1], easeOut);
  const startR: Rect = { x: -560, y: -540, w: 2200, h: 2200 * (SH / SW) };
  const print = mixRect(startR, FULL, arrive);
  const pk = print.w / SW;

  const landmarks = lerp(f, [E[1], E[1] + 26], [0, 1], easeOut);
  const iris = lerp(f, [E[2], E[3]], [0, 1], easeInOut);
  const frame = mixRect(FULL, CROP, iris);
  const lock = f >= E[3];
  const coverage = Math.round(interpolate(iris, [0, 1], [COVER_START, COVER_END]));
  const trace = lerp(f, [E[4], E[5] - 4], [0, 1], easeInOut);
  const lift = lerp(f, [E[5], E[6]], [0, 1], easeInOut);
  const white = lerp(f, [E[6], E[6] + 8], [0, 1], easeOut);
  const final = lerp(f, [E[6] + 12, E[7]], [0, 1]);
  const kb = Math.round(interpolate(f, [E[7], E[8]], [3400, KB], { easing: easeOut, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }));
  const typed = 'jee-main_photo.jpg'.slice(0, Math.max(0, Math.floor((f - E[8] - 2) / 1.4)));
  const checks = ['413 × 531 px', `${KB} KB`, 'JPEG', 'Plain white', `Face ${COVER_END}%`, 'Named'];

  // the whole stage breathes in 3D; once the background is gone the camera moves in on the photograph
  const ry = Math.sin(f / 70) * 4 * (1 - final);
  const hero = lerp(f, [E[6], E[7] + 6], [0, 1], easeInOut);
  const heroScale = 1 + hero * (HERO_SCALE - 1);
  const cx = CROP.x + CROP.w / 2;
  const cy = CROP.y + CROP.h / 2;

  return (
    <AbsoluteFill>
      <Studio warmth={1.1} tone="#050505" />
      <Beam x={300} y={-100} angle={-20} opacity={0.14} />
      <Beam x={880} y={-120} angle={18} opacity={0.07} color="200,215,255" />
      <Dust count={70} opacity={0.45} seed={9} />
      <AbsoluteFill style={{ transform: `translate(${sh.x + hero * (HERO_C.x - cx)}px, ${sh.y + hero * (HERO_C.y - cy)}px) scale(${heroScale})`, transformOrigin: `${cx}px ${cy}px`, perspective: 2000, opacity: f >= E[9] ? 0 : 1 }}>
        <AbsoluteFill style={{ transformStyle: 'preserve-3d', transform: `rotateY(${ry}deg)` }}>
          {/* the room: falls back into the dark as she lifts away from it */}
          <div
            style={{
              position: 'absolute', left: print.x, top: print.y, width: print.w, height: print.h,
              transform: `translateZ(${-lift * 500}px)`, filter: `blur(${lift * 10}px) brightness(${1 - lift * 0.75})`, opacity: 1 - white,
              boxShadow: '0 50px 120px rgba(0,0,0,0.8)',
            }}
          >
            <Img src={staticFile('photo/source.png')} style={{ width: '100%', height: '100%' }} />
          </div>
          {/* the white the exam asks for, inside the frame */}
          <div style={{ position: 'absolute', left: frame.x, top: frame.y, width: frame.w, height: frame.h, background: '#ffffff', opacity: white, boxShadow: white > 0 ? `0 0 ${120 * white}px rgba(255,240,225,0.35)` : undefined }} />
          {/* her, lifted on the engine's own matte */}
          <div
            style={{
              position: 'absolute', left: print.x, top: print.y, width: print.w, height: print.h, opacity: lift > 0 ? 1 - final : 0,
              transform: `translateZ(${lift * 90}px)`, filter: `drop-shadow(0 ${30 * lift}px ${40 * lift}px rgba(0,0,0,${0.6 * lift * (1 - white)}))`,
              clipPath: white > 0 ? `inset(${((frame.y - print.y) / print.h) * 100 * white}% ${((print.x + print.w - frame.x - frame.w) / print.w) * 100 * white}% ${((print.y + print.h - frame.y - frame.h) / print.h) * 100 * white}% ${((frame.x - print.x) / print.w) * 100 * white}%)` : undefined,
            }}
          >
            <Img src={staticFile('photo/cutout.png')} style={{ width: '100%', height: '100%' }} />
          </div>
          {/* the engine's actual output, settling into the frame */}
          <div style={{ position: 'absolute', left: frame.x, top: frame.y, width: frame.w, height: frame.h, opacity: final, transform: `translateZ(${90 * (1 - final)}px)` }}>
            <Img src={staticFile('photo/prepared.jpg')} style={{ width: '100%', height: '100%' }} />
          </div>

          {/* overlays live in the print's space */}
          <svg width={1080} height={1350} style={{ position: 'absolute', left: 0, top: 0, overflow: 'visible' }}>
            <g transform={`translate(${print.x - PRINT.x * (pk / k)}, ${print.y - PRINT.y * (pk / k)}) scale(${pk / k})`}>
              {/* landmarks */}
              {POINTS.map(([x, y], i) => {
                const v = Math.max(0, Math.min(1, landmarks * POINTS.length * 1.3 - i * 1.0));
                return <circle key={i} cx={x} cy={y} r={3.2} fill={C.signal} opacity={v * (1 - iris * 0.7) * (1 - lift)} />;
              })}
              {/* the matte outline, traced */}
              <path d={contourPath} fill="none" stroke={C.signal} strokeWidth={7} pathLength={1} strokeDasharray={1} strokeDashoffset={1 - trace} opacity={(1 - white) * (trace > 0 ? 1 : 0)} style={{ filter: 'drop-shadow(0 0 8px rgba(240,78,35,0.9))' }} />
            </g>
          </svg>
          {/* head box */}
          <Brackets r={{ x: X(head.left), y: Y(head.top), w: (head.right - head.left) * k, h: (head.bottom - head.top) * k }} color={C.paper} len={30} w={3} o={fade(f, E[1] + 10, 6) * (1 - iris)} />
          {/* the crop frame: the iris closing to the exam's ratio */}
          <div style={{ position: 'absolute', left: frame.x, top: frame.y, width: frame.w, height: frame.h, boxShadow: `0 0 0 3000px rgba(0,0,0,${0.62 * iris * (1 - white)})`, opacity: f >= E[2] ? 1 : 0 }} />
          <Brackets r={frame} color={lock ? C.signal : C.paper} len={lock ? 56 : 40} w={lock ? 7 : 4} o={f >= E[2] ? 1 : 0} />
          {lock ? (
            <>
              {/* eye line and centre, as the engine composes them */}
              <div style={{ position: 'absolute', left: frame.x, top: frame.y + frame.h * 0.507, width: frame.w, borderTop: '2px dashed rgba(240,78,35,0.8)', opacity: fade(f, E[3], 4) * (1 - white) }} />
              <div style={{ position: 'absolute', left: frame.x + frame.w / 2, top: frame.y, height: frame.h, borderLeft: '2px dashed rgba(250,249,246,0.45)', opacity: fade(f, E[3], 4) * (1 - white) }} />
              <div style={{ position: 'absolute', left: frame.x, top: frame.y - 54, fontFamily: F.display, fontWeight: 900, fontSize: 46, color: C.signal, opacity: fade(f, E[3], 4) }}>413 × 531 PX</div>
            </>
          ) : null}
          {/* the filename, typed under the photograph */}
          <div style={{ position: 'absolute', left: frame.x + frame.w / 2, top: frame.y + frame.h + 16, transform: 'translateX(-50%)', whiteSpace: 'nowrap', fontFamily: F.type, fontSize: 30, color: C.paper, opacity: f > E[8] ? 1 : 0 }}>
            {typed}
            <span style={{ color: C.signal, opacity: Math.floor(f / 5) % 2 }}>_</span>
          </div>
        </AbsoluteFill>
      </AbsoluteFill>

      {/* the steps, as an instrument would label them */}
      <Step n="01" t="Find the face" f={f} at={E[1]} until={E[2]} />
      <Step n="02" t="Frame it to the rule" f={f} at={E[2]} until={E[4]} />
      <Step n="03" t="Lift the background" f={f} at={E[4]} until={E[7]} />
      <Step n="04" t="Just under the limit" f={f} at={E[7]} until={E[8] + 6} />
      <Step n="05" t="Name it. Check it." f={f} at={E[8] + 6} until={E[9] + 20} />

      {/* readouts */}
      <div style={{ opacity: f < E[4] ? 1 : 1 - lerp(f, [E[4], E[4] + 8], [0, 1]) }}>
        <Readout label="FACE COVERAGE · RULE ≥ 80%" value={`${coverage}%`} good={iris > 0.98} f={f} at={E[2]} />
      </div>
      <div style={{ opacity: f < E[7] ? fade(f, E[5], 6) : 1 - lerp(f, [E[7], E[7] + 6], [0, 1]) }}>
        <Readout label="BACKGROUND" value={white > 0.5 ? 'EXAM WHITE' : 'BEDROOM'} good={white > 0.5} f={f} at={E[5]} />
      </div>
      <div style={{ opacity: f < E[8] + 8 ? 1 : 1 - lerp(f, [E[8] + 8, E[8] + 14], [0, 1]) }}>
        <Readout label="FILE SIZE · LIMIT 200 KB" value={kb > 999 ? `${(kb / 1000).toFixed(1)} MB` : `${kb} KB`} good={f >= E[8]} f={f} at={E[7]} size={150} />
      </div>
      {/* the final checks */}
      <div style={{ position: 'absolute', left: 64, top: 1118, display: 'grid', gridTemplateColumns: 'repeat(3, auto)', gap: '10px 28px', opacity: 1 - lerp(f, [E[9], E[9] + 10], [0, 1]), transform: `translateY(${lerp(f, [E[9], E[9] + 10], [0, 40], easeIn)}px)` }}>
        {checks.map((c, i) => (
          <div key={c} style={{ fontFamily: F.body, fontWeight: 700, fontSize: 32, color: C.paper, opacity: f >= E[8] + 14 + i * 3 ? 1 : 0 }}>
            <span style={{ color: '#5fd38d' }}>✓</span> {c}
          </div>
        ))}
      </div>
      <Flare x={CROP.x + CROP.w / 2} y={CROP.y} intensity={Math.max(0, 1 - Math.abs(f - E[6]) / 8)} color="255,240,225" />
      <Flare x={CROP.x + CROP.w} y={CROP.y + CROP.h / 2} intensity={f >= E[3] ? Math.max(0, 1 - (f - E[3]) / 8) * 0.8 : 0} />
      {void easeIn}
    </AbsoluteFill>
  );
};
