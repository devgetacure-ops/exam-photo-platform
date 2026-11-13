import React from 'react';
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { C, F } from '../kit/theme';
import { Camera, Grade, PaperTexture, Vignette } from '../kit/lens';
import { Clock, Phone } from '../kit/props';
import { easeIn, easeInOut, easeOut, fade, lerp, settle } from '../kit/motion';

// ============================================================================
// ACT 2 — The rewind, then the wall of examinations.
// ============================================================================

// ---- The rewind: the only whip in the film --------------------------------
const Rewind: React.FC = () => {
  const f = useCurrentFrame();
  // 2:40 AM back to 11:14 PM: 206 minutes unwound, fast then slowing into place
  const t = lerp(f, [0, 70], [0, 1], easeInOut);
  const minutes = 26 * 60 + 40 - t * 206;
  const warm = lerp(f, [40, 90], [0, 1]);
  const blur = Math.sin(t * Math.PI) * 6;
  const whiteFlash = interpolate(f, [70, 74, 86], [0, 0.9, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return (
    <AbsoluteFill style={{ background: '#0f1318' }}>
      <AbsoluteFill style={{ background: `radial-gradient(ellipse 60% 50% at 50% 50%, rgba(255,170,90,${0.35 * warm}), transparent 70%)` }} />
      <Camera scale={lerp(f, [0, 90], [1.05, 0.96])} rotate={Math.sin(t * Math.PI) * -4} blur={blur * 0.25}>
        <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
          {/* motion trail: three ghost hands of the past few frames */}
          <div style={{ position: 'relative', width: 600, height: 600 }}>
            {[3, 2, 1, 0].map((k) => (
              <div key={k} style={{ position: 'absolute', inset: 0, opacity: k === 0 ? 1 : 0.18 / k }}>
                <Clock minutes={minutes + k * 9 * Math.sin(t * Math.PI)} size={600} face={warm > 0.5 ? '#efe7d6' : '#c9ced3'} />
              </div>
            ))}
          </div>
        </AbsoluteFill>
      </Camera>
      <Grade tone="cold" amount={1 - warm} />
      <Grade tone="warm" amount={warm} />
      <Vignette strength={0.75} />
      <AbsoluteFill style={{ background: '#fff4e4', opacity: whiteFlash }} />
    </AbsoluteFill>
  );
};

const SameNight: React.FC = () => {
  const f = useCurrentFrame();
  const words = ['SAME', 'NIGHT.', 'AGAIN.'];
  return (
    <AbsoluteFill style={{ background: C.ink, alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
        {words.map((w, i) => {
          const a = fade(f, 4 + i * 9, 6);
          return (
            <div
              key={w}
              style={{
                fontFamily: F.display,
                fontWeight: 900,
                fontSize: 210,
                lineHeight: 0.84,
                color: i === 2 ? C.ink : C.paper,
                background: i === 2 ? C.signal : 'transparent',
                padding: i === 2 ? '18px 22px 0' : 0,
                opacity: a,
                transform: `translateY(${(1 - a) * 30}px)`,
              }}
            >
              {w}
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ---- The wall: every big examination, biggest first ------------------------
// Ordered roughly by candidate volume. Every line is counted from examples/rules (2026-11-13).
export const WALL: { name: string; body: string; spec: string }[] = [
  { name: 'RRB NTPC', body: 'Railway Recruitment Boards', spec: 'Photo · Signature · ID · Certificate' },
  { name: 'NEET (UG)', body: 'National Testing Agency', spec: 'Photo · Signature · Thumb · Certificates' },
  { name: 'GATE', body: 'IIT · Organising Institute', spec: 'Photo · Signature · ID · Certificates' },
  { name: 'UPSC CSE', body: 'Union Public Service Commission', spec: 'Photographs · Signature' },
  { name: 'CUET (UG)', body: 'National Testing Agency', spec: 'Photo · Signature · ID · Certificates' },
  { name: 'IBPS PO', body: 'IBPS', spec: 'Photo · Signature · Thumb · Declaration' },
  { name: 'CAT', body: 'Indian Institutes of Management', spec: 'Photo · Signature · Thumb' },
  { name: 'JEE (MAIN) 2027', body: 'National Testing Agency', spec: 'Photo · Signature · ID · Certificates' },
  { name: 'CLAT', body: 'Consortium of NLUs', spec: 'Photo · Signature' },
  { name: 'SBI PO', body: 'State Bank of India', spec: 'Photo · Signature · Thumb · Declaration' },
  { name: 'NDA', body: 'Union Public Service Commission', spec: 'Photographs · Signature' },
  { name: 'NEET (PG)', body: 'NBEMS', spec: 'Photo · Signature · Thumb · Certificate' },
  { name: 'CTET', body: 'CBSE', spec: 'Photo · Signature' },
  { name: 'CUET (PG)', body: 'National Testing Agency', spec: 'Photo · Signature · Certificates' },
  { name: 'AFCAT', body: 'Indian Air Force', spec: 'Photo · Signature · Thumb' },
];

const ExamCard: React.FC<{ e: (typeof WALL)[number]; hot?: boolean; scale?: number }> = ({ e, hot, scale = 1 }) => (
  <div
    style={{
      width: 400 * scale,
      padding: `${22 * scale}px ${26 * scale}px`,
      background: C.paper,
      border: `${3 * scale}px solid ${C.ink}`,
      boxShadow: `${7 * scale}px ${7 * scale}px 0 ${hot ? C.signal : C.ink}`,
    }}
  >
    <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 15 * scale, letterSpacing: '0.09em', textTransform: 'uppercase', color: C.ink55 }}>
      {e.body}
    </div>
    <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 54 * scale, lineHeight: 0.9, color: C.ink, marginTop: 8 * scale }}>{e.name}</div>
    <div style={{ fontFamily: F.body, fontWeight: 500, fontSize: 19 * scale, color: C.ink70, marginTop: 10 * scale }}>{e.spec}</div>
  </div>
);

/** The phone's search, rebuilt from the product's own components and tokens. */
const SearchScreen: React.FC<{ typed: string; results: number }> = ({ typed, results }) => {
  const matches = WALL.filter((e) => typed && e.name.startsWith(typed.toUpperCase())).slice(0, 3);
  const list = typed ? matches : WALL.slice(0, 4);
  return (
    <div style={{ position: 'absolute', inset: 0, background: C.paper, fontFamily: F.body }}>
      <div style={{ padding: '70px 26px 18px', borderBottom: `3px solid ${C.ink}` }}>
        <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 13, letterSpacing: '0.09em', color: C.ink55 }}>FIND YOUR EXAMINATION</div>
        <div style={{ marginTop: 12, border: `3px solid ${C.ink}`, boxShadow: `5px 5px 0 ${C.ink}`, padding: '14px 16px', fontSize: 24, fontWeight: 600, color: typed ? C.ink : C.ink40, display: 'flex', alignItems: 'center', gap: 12 }}>
          <svg width="22" height="22" viewBox="0 0 24 24"><circle cx="10" cy="10" r="7" stroke={C.ink} strokeWidth="2.6" fill="none" /><line x1="15" y1="15" x2="21" y2="21" stroke={C.ink} strokeWidth="2.6" /></svg>
          {typed || 'SSC CGL, NEET UG, IBPS PO…'}
          {typed ? <span style={{ width: 2, height: 26, background: C.signal }} /> : null}
        </div>
      </div>
      <div style={{ padding: '16px 26px' }}>
        {list.map((e, i) => (
          <div key={e.name} style={{ padding: '16px 0', borderBottom: `2px solid ${C.hairline}`, opacity: Math.min(1, results - i) }}>
            <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 32, color: C.ink, lineHeight: 0.95 }}>{e.name}</div>
            <div style={{ fontSize: 16, color: C.ink55, marginTop: 4 }}>{e.body}</div>
          </div>
        ))}
      </div>
    </div>
  );
};

const ExamWall: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  // 0–60: phone search, empty → types "J"
  // 60–200: camera pulls out of the phone into the wall, the wall drifts, count runs
  // 200–300: camera pushes into JEE (MAIN) 2027, which fills the frame
  const typed = f < 40 ? '' : 'JEE'.slice(0, Math.min(3, Math.floor((f - 40) / 6) + 1));
  const pull = lerp(f, [56, 110], [1, 0], easeInOut); // 1 = inside the phone
  const push = lerp(f, [210, 290], [0, 1], easeIn);
  const wallScale = interpolate(pull, [0, 1], [0.62, 2.6]) * interpolate(push, [0, 1], [1, 3.2]);
  const drift = Math.min(f, 210) * 1.6;
  const count = Math.round(interpolate(f, [100, 190], [0, 770], { easing: easeOut, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }));
  const cols = 3;
  const hotIdx = 7;
  // where JEE sits, so the push lands on it
  // JEE sits dead centre of the grid, so the push simply zooms on the grid centre as it drifts.
  const focusY = 675 + 120 - drift * 0.4;
  return (
    <AbsoluteFill style={{ background: '#e9e3d6' }}>
      <PaperTexture opacity={0.5} />
      {/* the wall */}
      <Camera scale={wallScale} origin={`540px ${focusY}px`}>
        <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', opacity: 1 - pull * 0.9 }}>
          <div style={{ display: 'grid', gridTemplateColumns: `repeat(${cols}, 400px)`, gap: '30px 40px', transform: `translateY(${120 - drift * 0.4}px) rotate(-6deg)` }}>
            {WALL.map((e, i) => {
              const s = settle(f, 70 + i * 3, fps, 18);
              return (
                <div key={e.name} style={{ opacity: s, transform: `translateY(${(1 - s) * 40}px)` }}>
                  <ExamCard e={e} hot={i === hotIdx && f > 160} />
                </div>
              );
            })}
          </div>
        </AbsoluteFill>
      </Camera>
      {/* the count, set in the product's display face */}
      <AbsoluteFill style={{ justifyContent: 'flex-end', padding: '0 64px 110px', opacity: fade(f, 100, 10, 205, 10) }}>
        <div style={{ background: C.ink, color: C.paper, padding: '26px 34px 18px', alignSelf: 'flex-start', boxShadow: `9px 9px 0 ${C.signal}` }}>
          <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 190, lineHeight: 0.8 }}>{count}+</div>
          <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 32, marginTop: 10 }}>exams. Each with its own rules, built in.</div>
        </div>
      </AbsoluteFill>
      {/* the phone we start inside */}
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', opacity: interpolate(pull, [0, 0.35], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }) }}>
        <Camera scale={interpolate(pull, [0, 1], [0.4, 1])}>
          <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
            <Phone width={500}>
              <SearchScreen typed={typed} results={f < 40 ? 4 : lerp(f, [44, 56], [0, 3])} />
            </Phone>
          </AbsoluteFill>
        </Camera>
      </AbsoluteFill>
      <Grade tone="warm" amount={0.35} />
      <Vignette strength={0.35} />
    </AbsoluteFill>
  );
};

export const ACT2 = 420;
export const Act2: React.FC = () => (
  <AbsoluteFill>
    <Sequence durationInFrames={90}><Rewind /></Sequence>
    <Sequence from={90} durationInFrames={30}><SameNight /></Sequence>
    <Sequence from={120} durationInFrames={300}><ExamWall /></Sequence>
  </AbsoluteFill>
);

export { ExamCard };
void easeOut;
