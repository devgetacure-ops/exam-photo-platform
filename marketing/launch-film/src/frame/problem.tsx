import React from 'react';
import { AbsoluteFill, Img, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { C, F } from '../kit/theme';
import { easeIn, easeInOut, easeOut, fade, lerp } from '../kit/motion';
import { Dust, Flare, HIT, Photo, Rect, Slam, Studio, mixRect, punch, shake } from './cinema';

// ============================================================================
// THE PROBLEM — rejected, the tools that pretend, the AI that imagines.
// Frames are absolute film frames (this component is not inside a Sequence offset).
// ============================================================================

export const R1: Rect = { x: 190, y: 560, w: 700, h: 520 }; // the portal's upload box
const RW: Rect = { x: 60, y: 160, w: 960, h: 1030 }; // the rival tool's window
const RB: Rect = { x: 120, y: 330, w: 840, h: 820 }; // the AI chat window

const SRC_FULL = { x: 0, y: 0, w: 1086, h: 1448 };

const Box: React.FC<{ r: Rect; children?: React.ReactNode; style?: React.CSSProperties }> = ({ r, children, style }) => (
  <div style={{ position: 'absolute', left: r.x, top: r.y, width: r.w, height: r.h, ...style }}>{children}</div>
);

const RedX: React.FC<{ size?: number; o?: number }> = ({ size = 44, o = 1 }) => (
  <svg width={size} height={size} viewBox="0 0 40 40" style={{ opacity: o, flex: 'none' }}>
    <rect width="40" height="40" fill={C.error} />
    <path d="M11 11 L29 29 M29 11 L11 29" stroke="#fff" strokeWidth="5" strokeLinecap="square" />
  </svg>
);

// ---- S1. Rejected ------------------------------------------------------------
const Hook: React.FC<{ f: number }> = ({ f }) => {
  const sh = shake(f, 22);
  const fall = lerp(f, [66, 92], [0, 1], easeIn);
  const drop = lerp(f, [-2, 1], [0, 1], easeIn); // the photo is already falling when we cut in
  const red = f >= HIT.reject ? lerp(f, [70, 88], [1, 0]) : 0;
  const photoH = 470;
  const photoW = photoH * 0.75;
  return (
    <AbsoluteFill style={{ transform: `translate(${sh.x}px, ${sh.y}px) scale(${sh.s * lerp(f, [0, 90], [1.0, 1.05])})` }}>
      {/* the portal, tilted under a cold light, falling away at the end */}
      <div style={{ position: 'absolute', inset: 0, perspective: 1800 }}>
        <div
          style={{
            position: 'absolute', left: 110, top: 430, width: 860, height: 800, background: '#e9edf2',
            transformOrigin: '50% 100%', transform: `rotateX(${8 + fall * 70}deg) translateY(${fall * 260}px)`,
            boxShadow: '0 60px 120px rgba(0,0,0,0.7)', opacity: 1 - fall,
          }}
        >
          <div style={{ background: '#1f3a68', color: '#fff', padding: '20px 28px', fontFamily: 'Arial', fontSize: 22, fontWeight: 700 }}>
            Online Application · Step 3 of 5 · Upload Documents
          </div>
          <div style={{ padding: '22px 80px', fontFamily: 'Arial', fontSize: 22, color: '#5c6670' }}>Upload Photograph *</div>
          <div style={{ position: 'absolute', left: 80, top: 680, right: 80, fontFamily: 'Arial', fontSize: 26, fontWeight: 700, color: C.error, opacity: f >= HIT.reject ? 1 : 0 }}>
            Photograph does not meet the specifications.
          </div>
        </div>
      </div>
      {/* the photo, slamming in */}
      <div
        style={{
          position: 'absolute', left: R1.x + (R1.w - photoW) / 2, top: R1.y + (R1.h - photoH) / 2 - (1 - drop) * 900,
          transform: `translateY(${fall * 420}px) rotateZ(${fall * 9}deg) scaleY(${f < 1 ? 1.25 : 1})`, opacity: 1 - fall,
          filter: f < 1 ? 'blur(6px)' : undefined, boxShadow: '0 30px 60px rgba(0,0,0,0.5)',
        }}
      >
        <Photo win={SRC_FULL} width={photoW} height={photoH} />
        <div style={{ position: 'absolute', inset: 0, background: C.error, mixBlendMode: 'multiply', opacity: 0.35 * (f >= HIT.reject ? 1 : 0) * (1 - fall) }} />
      </div>
      {/* the frame itself: dashed grey, then red, then it detaches and turns to light */}
      <Box
        r={R1}
        style={{
          border: f < HIT.reject ? '4px dashed #9aa4b0' : `${4 + red * 4}px solid ${red > 0.02 ? `rgba(209,43,43,${0.4 + red * 0.6})` : C.paper}`,
          boxShadow: `0 0 ${40 * (1 - red) * lerp(f, [70, 90], [0, 1])}px rgba(255,236,220,0.5)`,
        }}
      />
      {/* REJECTED. AGAIN. */}
      <div style={{ position: 'absolute', left: 64, top: 70, transform: `translateY(${-fall * 120}px)`, opacity: 1 - fall }}>
        <Slam font={F.display} size={176} color={C.error} split={punch(f)}>
          <span style={{ opacity: f >= 3 ? 1 : 0 }}>Rejected.</span>
        </Slam>
        <Slam font={F.display} size={176} color={C.paper} split={0} style={{ opacity: fade(f, 34, 3) }}>
          Again.
        </Slam>
      </div>
    </AbsoluteFill>
  );
};

// ---- S2. The tools that pretend -------------------------------------------
const EXAMS = ['JEE Main', 'NEET UG', 'SSC CGL', 'UPSC CSE', 'CUET UG', 'IBPS PO', 'JEE Main'];

const Rival: React.FC<{ f: number }> = ({ f }) => {
  const grow = lerp(f, [90, 108], [0, 1], easeOut);
  const squeeze = lerp(f, [246, 262], [0, 1], easeInOut);
  const r = squeeze > 0 ? mixRect(RW, RB, squeeze) : mixRect(R1, RW, grow);
  const sh = shake(f, 16);
  const exam = EXAMS[Math.min(EXAMS.length - 1, Math.max(0, Math.floor((f - 104) / 8)))];
  const content = Math.min(lerp(f, [92, 102], [0, 1]), 1 - squeeze);
  const p = { x: 70, y: 330, w: 390, h: 520 }; // the photo panel inside the window
  const items: [number, string, string][] = [
    [HIT.fail[0], 'You crop it yourself.', 'Guess the face. Guess the margins.'],
    [HIT.fail[1], 'Background stays.', 'Your room goes to the exam with you.'],
    [HIT.fail[2], 'Never compressed. Never renamed.', '3.4 MB · IMG_20250112.jpg · face coverage ignored'],
  ];
  return (
    <AbsoluteFill style={{ transform: `translate(${sh.x}px, ${sh.y}px)` }}>
      <Box r={r} style={{ border: `4px solid ${C.paper}`, background: `rgba(242,244,247,${Math.min(grow * 1.4, 1)})`, overflow: 'hidden', borderRadius: squeeze * 28 }}>
        <div style={{ position: 'absolute', left: 0, top: 0, width: RW.w - 8, opacity: content, transform: `scale(${r.w / RW.w})`, transformOrigin: '0 0', filter: squeeze > 0 ? `blur(${squeeze * 8}px)` : undefined }}>
          {/* chrome */}
          <div style={{ height: 70, background: '#dfe3e9', display: 'flex', alignItems: 'center', gap: 10, padding: '0 22px' }}>
            {['#ff5f57', '#febc2e', '#28c840'].map((c) => <div key={c} style={{ width: 16, height: 16, borderRadius: 9, background: c }} />)}
            <div style={{ marginLeft: 18, flex: 1, height: 40, borderRadius: 20, background: '#fff', display: 'flex', alignItems: 'center', padding: '0 20px', fontFamily: 'Arial', fontSize: 19, color: '#6a7480' }}>
              🔒 jee-main-photo-resizer.example
            </div>
          </div>
          <div style={{ padding: '30px 70px 0', fontFamily: 'Arial' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
              <div style={{ fontSize: 46, fontWeight: 800, color: '#1d2430' }}>{exam} Photo Resizer</div>
            </div>
            <div style={{ display: 'flex', gap: 16, marginTop: 22, alignItems: 'center' }}>
              <div style={{ padding: '14px 20px', borderRadius: 12, border: '2px solid #c9d3e0', background: '#fff', fontSize: 24, fontWeight: 700, color: '#1d2430', minWidth: 250 }}>
                Exam: {exam} ▾
              </div>
              <div style={{ padding: '14px 20px', borderRadius: 12, background: '#fff6cc', border: `3px solid ${f > 112 && f < 150 && Math.floor(f / 5) % 2 ? '#e0a800' : '#f0d36a'}`, fontSize: 24, fontWeight: 700, color: '#6b5400' }}>
                Size: 200 × 230 px
              </div>
            </div>
          </div>
          {/* the photo panel */}
          <div style={{ position: 'absolute', left: p.x, top: p.y, width: p.w, height: p.h, borderRadius: 14, overflow: 'hidden', boxShadow: '0 10px 30px rgba(30,50,90,0.2)' }}>
            <Photo win={SRC_FULL} width={p.w} height={p.h} />
            {/* background stays: the room glows red, she does not (the engine's own matte) */}
            <div style={{ position: 'absolute', inset: 0, background: 'repeating-linear-gradient(135deg, rgba(209,43,43,0.55) 0 14px, rgba(209,43,43,0.25) 14px 28px)', opacity: f >= HIT.fail[1] ? 1 : 0 }} />
            <Img src={staticFile('photo/cutout.png')} style={{ position: 'absolute', left: 0, top: 0, width: p.w, height: p.h, opacity: f >= HIT.fail[1] ? 1 : 0 }} />
            {/* the hand-made crop, wrong */}
            <div
              style={{
                position: 'absolute', left: 60 + Math.sin(f / 3) * 4, top: 90 + Math.cos(f / 4) * 4, width: 250, height: 290,
                border: '4px dashed #ffd400', transform: `rotate(${-4 + Math.sin(f / 5) * 2}deg)`, boxShadow: '0 0 0 999px rgba(0,0,0,0.35)',
                opacity: f >= HIT.fail[0] && f < HIT.fail[1] ? 1 : 0,
              }}
            />
          </div>
          {/* the failures */}
          <div style={{ position: 'absolute', left: 500, top: 340, width: 390, display: 'flex', flexDirection: 'column', gap: 34 }}>
            {items.map(([at, h, sub]) => {
              const v = lerp(f, [at, at + 5], [0, 1], easeOut);
              return (
                <div key={h} style={{ display: 'flex', gap: 16, opacity: v, transform: `translateX(${(1 - v) * 40}px) scale(${1 + (1 - v) * 0.3})`, transformOrigin: 'left center' }}>
                  <RedX />
                  <div>
                    <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 44, lineHeight: 0.9, color: '#1d2430', textTransform: 'uppercase' }}>{h}</div>
                    <div style={{ fontFamily: 'Arial', fontSize: 19, color: '#6a7480', marginTop: 8 }}>{sub}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </Box>
      {/* the line under the window */}
      <div style={{ position: 'absolute', left: 64, right: 64, top: 1210, textAlign: 'center', opacity: Math.min(fade(f, 112, 6), 1 - squeeze) }}>
        <Slam font={F.display} size={62} split={0}>
          Different exams. <span style={{ color: C.signal }}>Same old size.</span>
        </Slam>
      </div>
    </AbsoluteFill>
  );
};

// ---- S3. "Just use ChatGPT" ----------------------------------------------------
const AiAnswer: React.FC<{ f: number }> = ({ f }) => {
  const sh = shake(f, 14);
  const rush = lerp(f, [348, 362], [0, 1], easeIn);
  const ask = fade(f, 262, 6);
  const typing = f >= 272 && f < 280;
  const reply = fade(f, 280, 4);
  const notYou = f >= HIT.fail[3];
  const wrong = f >= HIT.fail[4];
  const img = 420;
  return (
    <AbsoluteFill style={{ transform: `translate(${sh.x}px, ${sh.y}px) scale(${1 + rush * 2.6})`, transformOrigin: '540px 760px', filter: rush > 0 ? `blur(${rush * 14}px)` : undefined, opacity: 1 - rush * 0.9 }}>
      <Box r={RB} style={{ border: `4px solid ${C.paper}`, borderRadius: 28, background: '#141414', overflow: 'hidden' }}>
        <div style={{ height: 76, borderBottom: '1px solid #2a2a2a', display: 'flex', alignItems: 'center', gap: 12, padding: '0 28px', fontFamily: F.body, fontWeight: 600, fontSize: 24, color: '#d8d8d8' }}>
          <span style={{ color: '#a98bff' }}>✦</span> Any AI chat
        </div>
        {/* the ask */}
        <div style={{ position: 'absolute', right: 28, top: 104, display: 'flex', gap: 12, alignItems: 'flex-end', opacity: ask, transform: `translateY(${(1 - ask) * 20}px)` }}>
          <Photo win={SRC_FULL} width={78} height={104} style={{ borderRadius: 10 }} />
          <div style={{ background: '#2f2f2f', color: '#f1f1f1', padding: '16px 22px', borderRadius: 22, fontFamily: F.body, fontSize: 26, maxWidth: 480 }}>
            Make this photo JEE Main compliant.
          </div>
        </div>
        {/* the answer */}
        <div style={{ position: 'absolute', left: 28, top: 250, fontFamily: F.body, fontSize: 26, color: '#e5e5e5' }}>
          {typing ? <span style={{ letterSpacing: 6 }}>{'•••'.slice(0, 1 + (Math.floor(f / 3) % 3))}</span> : <span style={{ opacity: reply }}>Here's your compliant photo! ✨</span>}
        </div>
        <div style={{ position: 'absolute', left: 28, top: 304, width: img, height: img, borderRadius: 18, overflow: 'hidden', opacity: reply, background: 'linear-gradient(160deg, #9ec5ff 0%, #4f7fd8 100%)' }}>
          {/* what a generator hands back: a smoothed, re-proportioned stranger on a studio blue */}
          <div style={{ position: 'absolute', left: -60, top: -40, width: img + 120, height: (img + 120) * 1.333, filter: 'blur(0.8px) saturate(1.3) brightness(1.1) contrast(0.9)', transform: 'scaleX(0.9) scaleY(1.04)' }}>
            <Img src={staticFile('photo/cutout.png')} style={{ width: '100%', height: '100%' }} />
          </div>
          <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(circle at 50% 35%, rgba(255,240,230,0.35), transparent 60%)', mixBlendMode: 'screen' }} />
          <div style={{ position: 'absolute', inset: 0, border: `6px solid ${C.error}`, borderRadius: 18, opacity: notYou ? 1 : 0 }} />
        </div>
        {/* the verdicts */}
        <div style={{ position: 'absolute', left: 476, top: 312, width: 330, display: 'flex', flexDirection: 'column', gap: 28 }}>
          <div style={{ display: 'flex', gap: 14, opacity: notYou ? 1 : 0, transform: `scale(${notYou ? 1 + Math.max(0, 6 - (f - HIT.fail[3])) * 0.05 : 1})`, transformOrigin: 'left center' }}>
            <RedX />
            <div>
              <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 52, lineHeight: 0.88, color: C.paper }}>NOT YOUR FACE.</div>
              <div style={{ fontFamily: F.body, fontSize: 21, color: '#9a9a9a', marginTop: 8 }}>It redraws you. The portal compares you.</div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: 14, opacity: wrong ? 1 : 0, transform: `scale(${wrong ? 1 + Math.max(0, 6 - (f - HIT.fail[4])) * 0.05 : 1})`, transformOrigin: 'left center' }}>
            <RedX />
            <div>
              <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 52, lineHeight: 0.88, color: C.paper }}>WRONG SIZE. OLD RULES.</div>
              <div style={{ fontFamily: F.body, fontSize: 21, color: '#9a9a9a', marginTop: 8 }}>1024 × 1024 · 1.8 MB · PNG · no filename · no idea what NTA changed this year</div>
            </div>
          </div>
        </div>
        <div style={{ position: 'absolute', left: 28, top: 750, fontFamily: F.body, fontSize: 22, color: '#8a8a8a', opacity: reply }}>
          Still need to resize, compress and rename it? Try a free online tool!
        </div>
      </Box>
      <div style={{ position: 'absolute', left: 64, right: 64, top: 1196, textAlign: 'center', opacity: fade(f, 268, 6) }}>
        <Slam font={F.display} size={70}>
          "Just use <span style={{ color: '#a98bff' }}>AI</span>."
        </Slam>
      </div>
    </AbsoluteFill>
  );
};

// ---- S3b. The verdict, in three lines -------------------------------------------
const Verdict: React.FC<{ f: number }> = ({ f }) => {
  const lines: [number, string, string][] = [
    [362, 'Tools guess.', C.paper],
    [375, 'AI imagines.', C.paper],
    [388, 'Portals reject.', C.error],
  ];
  const collapse = lerp(f, [398, 406], [0, 1], easeIn);
  return (
    <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
      <div style={{ transform: `scaleY(${1 - collapse * 0.985}) scaleX(${1 + collapse * 0.4})`, filter: collapse > 0 ? `brightness(${1 + collapse * 4})` : undefined }}>
        {lines.map(([at, t, c]) => {
          const v = lerp(f, [at, at + 4], [0, 1], easeOut);
          return (
            <div key={t} style={{ opacity: f >= at ? 1 : 0, transform: `translateX(${(1 - v) * -90}px)` }}>
              <Slam font={F.display} size={176} color={c} split={Math.max(0, 1 - (f - at) / 6)}>
                {t}
              </Slam>
            </div>
          );
        })}
      </div>
      <Flare x={540} y={675} intensity={collapse} color="255,240,225" />
    </AbsoluteFill>
  );
};

export const Problem: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill>
      <Studio warmth={f < 255 ? 0.5 : 0.8} tone="#050608" />
      <Dust count={40} opacity={0.35} seed={2} />
      {f < 92 ? <Hook f={f} /> : null}
      {f >= 88 && f < 264 ? <Rival f={f} /> : null}
      {f >= 262 && f < 364 ? <AiAnswer f={f} /> : null}
      {f >= 360 && f < 408 ? <Verdict f={f} /> : null}
      {void easeInOut}
      {void interpolate}
    </AbsoluteFill>
  );
};
