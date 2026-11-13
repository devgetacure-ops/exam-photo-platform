import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { C } from '../kit/theme';
import { rand } from '../kit/motion';

// ============================================================================
// The cinema kit for THE FRAME: light, haze, lens, impact. Every hit is on the score.
// ============================================================================

/** Hits detected in the score's impact stem (seconds × 30). */
export const HIT = {
  reject: 1,
  fail: [150, 195, 240, 285, 330],
  riser: 405,
  drop: 480,
  // THE_FRAME_FIELD: measured from the master (onsets at 17.25, 18, 19, 20 s)
  click: [518, 540, 570, 600],
  // 21, 22, 24, 26, 27, 29.25, 30, 31.07, 32, 34 s
  engine: [630, 660, 720, 780, 810, 878, 900, 932, 960, 1020],
  app: [1080, 1110, 1140, 1170, 1200, 1230],
  proof: [1260, 1290, 1320, 1350],
  logo: 1380,
  end: 1500,
};
const ALL_HITS = [HIT.reject, ...HIT.fail, HIT.drop, ...HIT.engine, ...HIT.proof, HIT.logo];
const HEAVY = new Set([HIT.reject, HIT.drop, HIT.logo, ...HIT.fail]);

/** 0..1 energy of the most recent hit, decaying over ~6 frames. */
export const punch = (f: number) => {
  let e = 0;
  for (const h of ALL_HITS) {
    if (f >= h && f < h + 18) e = Math.max(e, Math.exp(-(f - h) / (HEAVY.has(h) ? 5 : 3)) * (HEAVY.has(h) ? 1 : 0.45));
  }
  return e;
};

/** Camera shake from the score. */
export const shake = (f: number, amp = 14) => {
  const e = punch(f);
  return { x: (rand(f * 3.1) - 0.5) * 2 * amp * e, y: (rand(f * 7.7) - 0.5) * 2 * amp * e, s: 1 + 0.02 * e };
};

/** The studio: near-black, a warm key from upper left, haze, a floor that catches light. */
export const Studio: React.FC<{ key?: string; warmth?: number; children?: React.ReactNode; tone?: string }> = ({ warmth = 1, children, tone = '#060606' }) => (
  <AbsoluteFill style={{ background: tone }}>
    <AbsoluteFill style={{ background: `radial-gradient(ellipse 70% 55% at 30% 18%, rgba(255,150,90,${0.16 * warmth}) 0%, rgba(0,0,0,0) 70%)` }} />
    <AbsoluteFill style={{ background: 'radial-gradient(ellipse 90% 40% at 50% 105%, rgba(240,78,35,0.10) 0%, rgba(0,0,0,0) 70%)' }} />
    {children}
  </AbsoluteFill>
);

/** A volumetric beam, the kind a projector cuts through haze. */
export const Beam: React.FC<{ x: number; y: number; angle: number; length?: number; width?: number; opacity?: number; color?: string }> = ({
  x, y, angle, length = 1700, width = 520, opacity = 0.16, color = '255,214,170',
}) => (
  <div
    style={{
      position: 'absolute', left: x - width / 2, top: y, width, height: length,
      transformOrigin: '50% 0', transform: `rotate(${angle}deg)`,
      background: `linear-gradient(180deg, rgba(${color},${opacity}) 0%, rgba(${color},${opacity * 0.35}) 55%, rgba(${color},0) 100%)`,
      clipPath: 'polygon(46% 0, 54% 0, 100% 100%, 0 100%)', filter: 'blur(18px)', mixBlendMode: 'screen', pointerEvents: 'none',
    }}
  />
);

/** Dust drifting through the light. */
export const Dust: React.FC<{ count?: number; opacity?: number; seed?: number }> = ({ count = 60, opacity = 0.5, seed = 1 }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: 'none', mixBlendMode: 'screen' }}>
      {Array.from({ length: count }, (_, i) => {
        const r = (k: number) => rand(i * 13.7 + seed * 101 + k);
        const depth = 0.3 + r(1) * 0.7;
        const x = (r(2) * 1180 - 50 + f * (0.2 + r(3) * 0.5) * depth) % 1180;
        const y = (r(4) * 1450 - f * (0.15 + r(5) * 0.35) * depth + 1450) % 1450;
        const s = 1.5 + depth * 3.5;
        return <div key={i} style={{ position: 'absolute', left: x, top: y, width: s, height: s, borderRadius: 9, background: `rgba(255,225,190,${opacity * depth})`, filter: `blur(${(1 - depth) * 3}px)` }} />;
      })}
    </AbsoluteFill>
  );
};

/** Anamorphic flare: a long horizontal streak with a hot core. */
export const Flare: React.FC<{ x: number; y: number; intensity: number; color?: string; length?: number }> = ({ x, y, intensity, color = '255,120,70', length = 1400 }) =>
  intensity <= 0.01 ? null : (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 1080, height: 1350, pointerEvents: 'none', mixBlendMode: 'screen' }}>
      <div style={{ position: 'absolute', left: x - length / 2, top: y - 3, width: length, height: 6, background: `linear-gradient(90deg, rgba(${color},0), rgba(${color},${0.9 * intensity}) 50%, rgba(${color},0))`, filter: 'blur(2px)' }} />
      <div style={{ position: 'absolute', left: x - length / 3, top: y - 14, width: (length * 2) / 3, height: 28, background: `linear-gradient(90deg, rgba(${color},0), rgba(${color},${0.35 * intensity}) 50%, rgba(${color},0))`, filter: 'blur(10px)' }} />
      <div style={{ position: 'absolute', left: x - 60, top: y - 60, width: 120, height: 120, borderRadius: 999, background: `radial-gradient(circle, rgba(255,240,220,${intensity}) 0%, rgba(${color},${0.4 * intensity}) 30%, rgba(0,0,0,0) 70%)` }} />
    </div>
  );

/** Film finish: grain, vignette, a whisper of halation. Applied once over the whole film. */
export const FilmFinish: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: 'none' }}>
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 75% at 50% 48%, rgba(0,0,0,0) 55%, rgba(0,0,0,${f >= HIT.logo ? 0.18 : 0.6}) 100%)` }} />
      <AbsoluteFill style={{ mixBlendMode: 'overlay', opacity: 0.09 }}>
        <svg width="100%" height="100%">
          <filter id={`fg${f}`}>
            <feTurbulence type="fractalNoise" baseFrequency="0.85" numOctaves={2} seed={f % 113} stitchTiles="stitch" />
            <feColorMatrix type="saturate" values="0" />
          </filter>
          <rect width="100%" height="100%" filter={`url(#fg${f})`} />
        </svg>
      </AbsoluteFill>
      {/* the flash on heavy hits */}
      <AbsoluteFill style={{ background: '#fff4ea', opacity: Math.max(0, punch(f) - 0.55) * 0.35, mixBlendMode: 'screen' }} />
    </AbsoluteFill>
  );
};

/** Big display type with an RGB split that spikes on hits. */
export const Slam: React.FC<{ children: React.ReactNode; size: number; color?: string; split?: number; style?: React.CSSProperties; font: string }> = ({
  children, size, color = C.paper, split = 0, style, font,
}) => (
  <div
    style={{
      fontFamily: font, fontWeight: 900, fontSize: size, lineHeight: 0.84, color, textTransform: 'uppercase', letterSpacing: '0.005em',
      textShadow: split > 0.05 ? `${split * 6}px 0 rgba(255,40,40,0.75), ${-split * 6}px 0 rgba(40,160,255,0.75)` : undefined,
      ...style,
    }}
  >
    {children}
  </div>
);

/** The photograph, cropped by a window in its own pixel space. */
export const Photo: React.FC<{
  file?: string;
  srcW?: number;
  srcH?: number;
  /** the window into the source, in source pixels */
  win: { x: number; y: number; w: number; h: number };
  width: number;
  height: number;
  style?: React.CSSProperties;
}> = ({ file = 'photo/source.png', srcW = 1086, srcH = 1448, win, width, height, style }) => {
  const sx = width / win.w;
  const sy = height / win.h;
  return (
    <div style={{ width, height, overflow: 'hidden', position: 'relative', ...style }}>
      <Img src={staticFile(file)} style={{ position: 'absolute', left: -win.x * sx, top: -win.y * sy, width: srcW * sx, height: srcH * sy, maxWidth: 'none' }} />
    </div>
  );
};

/** A lerp across rectangles, so a frame can travel from one shape into the next. */
export type Rect = { x: number; y: number; w: number; h: number };
export const mixRect = (a: Rect, b: Rect, t: number): Rect => ({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t, w: a.w + (b.w - a.w) * t, h: a.h + (b.h - a.h) * t });
