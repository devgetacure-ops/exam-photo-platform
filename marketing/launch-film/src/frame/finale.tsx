import React from 'react';
import { AbsoluteFill, Img, staticFile, useCurrentFrame } from 'remotion';
import { C, F } from '../kit/theme';
import { easeIn, easeInOut, easeOut, fade, lerp, rand } from '../kit/motion';
import { Wordmark } from '../kit/props';
import { LivePage, PageKey } from '../kit/screen';
import { Beam, Dust, Flare, HIT, Rect, Slam, Studio, mixRect, punch, shake } from './cinema';
import { Phone3D } from './phone3d';
import data from '../../public/photo/landmarks.json';

// ============================================================================
// THE KIT, THE APP, THE PROOF, THE NAME.
// ============================================================================

const KB = Math.round((data.final.bytes as number) / 1024);
import { PHOTO_END } from './engine';
const SIG: Rect = { x: 110, y: 470, w: 860, h: 330 };
const DOC: Rect = { x: 290, y: 300, w: 500, h: 680 };
const KIT: Rect = { x: 110, y: 260, w: 860, h: 820 };
const PHONE = { x: 560, y: 210, w: 410 };
const PH = PHONE.w * (844 / 390);
const SCREEN: Rect = { x: PHONE.x, y: PHONE.y, w: PHONE.w, h: PH };

const A = HIT.app; // 1080 1110 1140 1170 1200 1230

/** A card that flips and changes shape at the moment it is edge-on. */
const FlipCard: React.FC<{ f: number }> = ({ f }) => {
  // flip 1: photo → signature (1020–1050); flip 2: signature → document (1062–1086)
  const t1 = lerp(f, [1020, 1050], [0, 1], easeInOut);
  const t2 = lerp(f, [1062, 1086], [0, 1], easeInOut);
  const phase = t2 > 0 ? 2 : 1;
  const t = phase === 1 ? t1 : t2;
  const from = phase === 1 ? PHOTO_END : SIG;
  const to = phase === 1 ? SIG : DOC;
  const r = mixRect(from, to, t);
  const angle = t * 180;
  const showBack = t >= 0.5;
  const face = phase === 1 ? (showBack ? 'sig' : 'photo') : showBack ? 'doc' : 'sig';
  const clean = lerp(f, [1050, 1060], [0, 1], easeInOut);
  const lift = Math.sin(t * Math.PI);
  return (
    <div style={{ position: 'absolute', left: 0, top: 0, width: 1080, height: 1350, perspective: 1800 }}>
      <div
        style={{
          position: 'absolute', left: r.x, top: r.y, width: r.w, height: r.h,
          transform: `translateZ(${lift * 220}px) rotateY(${showBack ? angle - 180 : angle}deg)`,
          boxShadow: `0 ${30 + lift * 40}px ${70 + lift * 60}px rgba(0,0,0,0.6)`, background: '#fff', overflow: 'hidden',
        }}
      >
        {face === 'photo' ? <Img src={staticFile('photo/prepared.jpg')} style={{ width: '100%', height: '100%' }} /> : null}
        {face === 'sig' ? (
          <div style={{ position: 'absolute', inset: 0 }}>
            <div style={{ position: 'absolute', inset: 0, background: 'linear-gradient(115deg,#b9ad8c 0%,#d8cfb4 45%,#8e8670 100%)' }} />
            <div style={{ position: 'absolute', right: -40, top: -60, width: 420, height: 380, background: 'radial-gradient(ellipse at 70% 30%, rgba(30,24,15,0.5), transparent 65%)', opacity: 1 - clean }} />
            <div style={{ position: 'absolute', inset: 0, background: '#fff', clipPath: `inset(0 ${(1 - clean) * 100}% 0 0)` }} />
            <svg width="100%" height="100%" viewBox="0 0 860 330" preserveAspectRatio="none" style={{ position: 'absolute', inset: 0 }}>
              <path d="M120 220 C 160 90, 220 90, 210 200 C 204 260, 250 150, 290 160 C 330 170, 310 230, 350 200 C 390 170, 410 120, 440 190 C 460 240, 510 140, 550 170 C 590 200, 640 160, 720 150" stroke={clean > 0.5 ? '#0b1550' : '#24306a'} strokeWidth={clean > 0.5 ? 7 : 5} fill="none" strokeLinecap="round" opacity={0.7 + clean * 0.3} />
            </svg>
            <div style={{ position: 'absolute', left: `${clean * 100}%`, top: 0, bottom: 0, width: 5, background: C.signal, boxShadow: `0 0 24px ${C.signal}`, opacity: clean > 0 && clean < 1 ? 1 : 0 }} />
          </div>
        ) : null}
        {face === 'doc' ? <Doc title="CLASS X CERTIFICATE" seed={1} /> : null}
      </div>
    </div>
  );
};

const Doc: React.FC<{ title: string; seed: number; scale?: number }> = ({ title, seed, scale = 1 }) => (
  <div style={{ position: 'absolute', inset: 0, background: '#fbf8f0', padding: 44 * scale, borderTop: `${14 * scale}px solid ${C.ink}` }}>
    <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 40 * scale, color: C.ink, lineHeight: 0.9 }}>{title}</div>
    {Array.from({ length: 10 }, (_, k) => (
      <div key={k} style={{ height: 9 * scale, background: '#d3ccbc', marginTop: 26 * scale, width: `${50 + rand(k + seed * 17) * 45}%` }} />
    ))}
    <div style={{ position: 'absolute', right: 40 * scale, bottom: 40 * scale, width: 90 * scale, height: 90 * scale, borderRadius: 99, border: `${5 * scale}px solid rgba(193,55,14,0.5)` }} />
  </div>
);

/** The certificates fan out in depth, then become one PDF. */
const Fan: React.FC<{ f: number }> = ({ f }) => {
  const fan = lerp(f, [1086, 1098], [0, 1], easeOut);
  const merge = lerp(f, [A[1] - 12, A[1] - 2], [0, 1], easeIn);
  const titles = ['CLASS X CERTIFICATE', 'IDENTITY PROOF', 'PWD / UDID', 'PHYSICAL LIMITATION'];
  return (
    <div style={{ position: 'absolute', inset: 0, perspective: 1800 }}>
      {titles.map((t, i) => {
        const spread = (i - 1.5) * fan * (1 - merge);
        return (
          <div
            key={t}
            style={{
              position: 'absolute', left: DOC.x, top: DOC.y, width: DOC.w, height: DOC.h, transformOrigin: '50% 100%',
              transform: `translateX(${spread * 150}px) translateZ(${-Math.abs(spread) * 120 + i * 2}px) rotateZ(${spread * 9}deg) rotateY(${spread * -14}deg)`,
              boxShadow: '0 30px 60px rgba(0,0,0,0.55)', overflow: 'hidden',
            }}
          >
            <Doc title={t} seed={i + 1} />
          </div>
        );
      })}
      <div style={{ position: 'absolute', left: DOC.x - 60, top: DOC.y + DOC.h + 30, width: DOC.w + 120, textAlign: 'center', opacity: fade(f, A[1], 4) }}>
        <Slam font={F.display} size={58} color={C.paper}>
          One PDF · 4 pages <span style={{ color: '#5fd38d' }}>✓</span>
        </Slam>
      </div>
    </div>
  );
};

const FILES = ['jee-main_photo.jpg', 'jee-main_signature.jpg', 'jee-main_class-x.pdf', 'jee-main_id-proof.jpg', 'jee-main_pwd.pdf', 'jee-main_physical.pdf'];

/** The kit: one sheet with every file, then it becomes the phone. */
const Kit: React.FC<{ f: number }> = ({ f }) => {
  const open = lerp(f, [A[1] + 4, A[1] + 16], [0, 1], easeOut);
  const toPhone = lerp(f, [A[2] - 2, A[2] + 10], [0, 1], easeInOut);
  const r = mixRect(mixRect(DOC, KIT, open), SCREEN, toPhone);
  return (
    <div style={{ position: 'absolute', left: r.x, top: r.y, width: r.w, height: r.h, background: C.paper, boxShadow: '0 40px 90px rgba(0,0,0,0.6)', overflow: 'hidden', opacity: toPhone < 1 ? 1 : 0 }}>
      <div style={{ width: KIT.w, height: KIT.h, transform: `scale(${r.w / KIT.w}, ${r.h / KIT.h})`, transformOrigin: '0 0', padding: '44px 50px' }}>
        <div style={{ fontFamily: F.body, fontWeight: 700, fontSize: 22, letterSpacing: '0.12em', color: C.ink55 }}>JEE (MAIN) 2027 · YOUR KIT</div>
        <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 92, lineHeight: 0.86, color: C.ink, marginTop: 10 }}>6 FILES. READY.</div>
        <div style={{ marginTop: 26 }}>
          {FILES.map((n, i) => {
            const v = lerp(f, [A[1] + 8 + i * 2, A[1] + 14 + i * 2], [0, 1], easeOut);
            return (
              <div key={n} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '17px 0', borderBottom: `3px solid ${C.ink}`, opacity: v, transform: `translateX(${(1 - v) * 60}px)` }}>
                <span style={{ fontFamily: F.body, fontWeight: 700, fontSize: 34, color: C.ink }}>{n}</span>
                <span style={{ fontFamily: F.body, fontWeight: 700, fontSize: 30, color: C.okLine }}>✓</span>
              </div>
            );
          })}
        </div>
        <div style={{ marginTop: 30, background: C.signal, border: `4px solid ${C.ink}`, boxShadow: `8px 8px 0 ${C.ink}`, padding: '22px 0', textAlign: 'center', fontFamily: F.body, fontWeight: 700, fontSize: 36, color: '#fff' }}>
          Download all
        </div>
      </div>
    </div>
  );
};

/** The app: the phone turns between real screens on the beat. */
const SHOTS: { at: number; page: PageKey; scroll: number }[] = [
  { at: A[2], page: 'jee', scroll: 747 },
  { at: A[3], page: 'home', scroll: 0 },
  { at: A[4], page: 'jeeHi', scroll: 0 },
  { at: A[5], page: 'jee', scroll: 0 },
];

const BeforeAfter: React.FC<{ f: number; w: number }> = ({ f, w }) => {
  const pos = lerp(f, [A[5] + 2, A[5] + 18], [0.9, 0.12], easeInOut) + lerp(f, [A[5] + 20, 1258], [0, 0.35], easeInOut);
  const h = w * 1.2857;
  return (
    <div style={{ position: 'absolute', inset: 0, background: C.paper, padding: `${w * 0.2}px ${w * 0.05}px 0` }}>
      <div style={{ fontFamily: F.body, fontWeight: 700, fontSize: w * 0.034, letterSpacing: '0.1em', color: C.ink55 }}>PHOTOGRAPH · READY</div>
      <div style={{ position: 'relative', marginTop: w * 0.03, width: w * 0.9, height: h * 0.9, border: `3px solid ${C.ink}`, overflow: 'hidden' }}>
        {/* before: the same crop, from her original */}
        <div style={{ position: 'absolute', inset: 0 }}>
          <Img src={staticFile('photo/source.png')} style={{ position: 'absolute', width: (1086 / 427) * w * 0.9, left: -(390 / 427) * w * 0.9, top: -(362 / 549) * h * 0.9 }} />
        </div>
        <div style={{ position: 'absolute', inset: 0, clipPath: `inset(0 0 0 ${pos * 100}%)` }}>
          <Img src={staticFile('photo/prepared.jpg')} style={{ width: '100%', height: '100%' }} />
        </div>
        <div style={{ position: 'absolute', top: 0, bottom: 0, left: `${pos * 100}%`, width: 4, marginLeft: -2, background: C.ink }}>
          <div style={{ position: 'absolute', top: '50%', left: -18, width: 36, height: 36, marginTop: -18, background: C.signal, border: `3px solid ${C.ink}` }} />
        </div>
      </div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: w * 0.03, fontFamily: F.body, fontWeight: 700, fontSize: w * 0.04 }}>
        <span>413 × 531 px</span><span>{KB} KB</span><span>JPEG</span>
      </div>
    </div>
  );
};

const App: React.FC<{ f: number }> = ({ f }) => {
  // the body forms only once the kit has landed in the screen
  const form = lerp(f, [A[2] + 9, A[2] + 18], [0, 1], easeOut);
  if (f < A[2] + 10) return null;
  let idx = 0;
  SHOTS.forEach((s, i) => { if (f >= s.at) idx = i; });
  const shot = SHOTS[idx];
  // a whip turn on every beat: 0 → 360, the screen swaps when edge-on
  const since = f - shot.at;
  const whip = idx > 0 && since < 8 ? lerp(since, [0, 8], [-180, 0], easeOut) : 0;
  const ry = -14 + Math.sin(f / 30) * 4 + whip;
  const leave = lerp(f, [HIT.proof[0] - 4, HIT.proof[0] + 10], [0, 1], easeIn);
  const words: [number, string, string, string?][] = [
    [A[2], 'Feels like', C.paper],
    [A[2] + 5, 'an app.', C.paper],
    [A[3], 'Built like one.', C.signal],
    [A[4], 'हिंदी में भी।', C.paper, F.hindi],
    [A[5], 'Your face. Untouched.', C.paper],
  ];
  return (
    <>
      <div style={{ position: 'absolute', left: 0, top: 0, width: 1080, height: 1350, perspective: 2200, transform: `translateZ(0) scale(${1 - leave * 0.8})`, transformOrigin: '765px 675px', opacity: 1 - leave, filter: Math.abs(whip) > 40 ? `blur(${Math.abs(whip) / 30}px)` : undefined }}>
        <div style={{ position: 'absolute', left: PHONE.x - PHONE.w * 0.04 * form, top: PHONE.y - PHONE.w * 0.04 * form, transformStyle: 'preserve-3d' }}>
          <Phone3D w={PHONE.w} ry={ry * form} rx={5 * form} bezel={form} glare={((f - A[2]) / 80) % 1.4}>
            <div style={{ position: 'absolute', inset: 0 }}>
              {idx === 3 ? <BeforeAfter f={f} w={PHONE.w} /> : <LivePage page={shot.page} width={PHONE.w} scroll={shot.scroll + (idx === 1 ? lerp(f, [A[3] + 8, A[4]], [0, 120]) : 0)} />}
            </div>
          </Phone3D>
        </div>
      </div>
      <div style={{ position: 'absolute', left: 64, top: 330, width: 470, opacity: 1 - leave }}>
        {words.map(([at, t, c, font]) => {
          const v = lerp(f, [at, at + 5], [0, 1], easeOut);
          const gone = at >= A[4] && f >= A[5] && at < A[5];
          return (
            <div key={t} style={{ opacity: f >= at && !gone ? 1 : 0, transform: `translateY(${(1 - v) * 24}px)`, marginBottom: font ? 10 : 0 }}>
              <Slam font={font ?? F.display} size={font ? 92 : 100} color={c} split={Math.max(0, 1 - (f - at) / 5) * 0.5} style={font ? { textTransform: 'none', lineHeight: 1.2 } : undefined}>
                {t}
              </Slam>
            </div>
          );
        })}
        <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 28, color: '#bdb6a8', marginTop: 24, opacity: f >= A[4] && f < A[5] ? 1 : 0 }}>
          More Indian languages coming soon.
        </div>
      </div>
    </>
  );
};

/** Four claims, four hits, stacking back into depth. */
const PROOF: { t: string; c: string }[] = [
  { t: '770+ exams.', c: C.paper },
  { t: 'Rules updated every cycle.', c: C.paper },
  { t: 'Free. No login.', c: C.signal },
  { t: "India's only one.", c: C.paper },
];

const Proof: React.FC<{ f: number }> = ({ f }) => {
  const collapse = lerp(f, [HIT.logo - 6, HIT.logo], [0, 1], easeIn);
  return (
    <div style={{ position: 'absolute', inset: 0, perspective: 1400 }}>
      {PROOF.map((p, i) => {
        const at = HIT.proof[i];
        if (f < at) return null;
        const age = PROOF.filter((_, j) => f >= HIT.proof[j]).length - 1 - i;
        const v = lerp(f, [at, at + 6], [0, 1], easeOut);
        const z = -age * 260;
        return (
          <div
            key={p.t}
            style={{
              position: 'absolute', left: 0, right: 0, top: 560, textAlign: 'center',
              transform: `translateZ(${z + (1 - v) * 500 - collapse * 900}px) translateY(${age * -250}px) scale(${1 - collapse * 0.5})`,
              opacity: (age === 0 ? 1 : Math.max(0.06, 0.3 - age * 0.08)) * (1 - collapse),
            }}
          >
            <Slam font={F.display} size={p.t.length > 18 ? 86 : 150} color={p.c} split={age === 0 ? Math.max(0, 1 - (f - at) / 6) : 0}>
              {p.t}
            </Slam>
          </div>
        );
      })}
    </div>
  );
};

/** The frame grows into the page, and the name is set on it. */
const End: React.FC<{ f: number }> = ({ f }) => {
  const grow = lerp(f, [HIT.logo, HIT.logo + 10], [0, 1], easeOut);
  const r = mixRect({ x: 440, y: 560, w: 200, h: 257 }, { x: -20, y: -20, w: 1120, h: 1390 }, grow);
  const reveal = lerp(f, [HIT.logo + 10, HIT.logo + 34], [0, 13], easeOut);
  return (
    <>
      <div style={{ position: 'absolute', left: r.x, top: r.y, width: r.w, height: r.h, background: C.paper, border: `${6 * (1 - grow) + 2}px solid ${C.paper}` }} />
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 54, opacity: grow }}>
        <div style={{ opacity: Math.min(1, reveal) }}>
          <Wordmark cell={104} reveal={reveal} />
        </div>
        <div style={{ textAlign: 'center', opacity: fade(f, HIT.logo + 30, 8) }}>
          <Slam font={F.display} size={118} color={C.ink}>Pick your exam.</Slam>
          <div style={{ display: 'inline-block', marginTop: 16, background: C.signal, padding: '14px 24px 2px' }}>
            <Slam font={F.display} size={118} color={C.paper}>Get the whole kit.</Slam>
          </div>
        </div>
        <div style={{ opacity: fade(f, HIT.logo + 52, 8), marginTop: 30, textAlign: 'center' }}>
          <span style={{ fontFamily: F.display, fontWeight: 900, fontSize: 66, color: C.paper, background: C.ink, padding: '14px 30px 4px', boxShadow: `8px 8px 0 ${C.signal}` }}>EXAMUPLOADKIT.COM</span>
          <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 30, color: C.ink55, marginTop: 30 }}>India's only complete exam upload kit.</div>
        </div>
      </AbsoluteFill>
    </>
  );
};

export const Finale: React.FC = () => {
  const f = useCurrentFrame();
  const sh = shake(f, 12);
  const atEnd = f >= HIT.logo;
  return (
    <AbsoluteFill>
      <Studio warmth={1.1} tone="#050505" />
      <Beam x={260} y={-80} angle={-22} opacity={0.12} />
      <Dust count={60} opacity={0.4} seed={13} />
      <AbsoluteFill style={{ transform: `translate(${sh.x}px, ${sh.y}px)` }}>
        {f < 1090 ? <FlipCard f={f} /> : null}
        {f >= 1086 && f < A[1] + 1 ? <Fan f={f} /> : null}
        {f >= A[1] && f < A[2] + 10 ? <Kit f={f} /> : null}
        {f >= A[2] - 2 && f < HIT.proof[0] + 12 ? <App f={f} /> : null}
        {f >= HIT.proof[0] && f < HIT.logo + 2 ? <Proof f={f} /> : null}
        {/* labels under the cards */}
        <div style={{ position: 'absolute', left: 0, right: 0, top: SIG.y + SIG.h + 40, textAlign: 'center', opacity: fade(f, 1052, 4, 1060, 4) }}>
          <Slam font={F.display} size={58} color={C.paper}>
            Signature · cleaned · 10–100 KB <span style={{ color: '#5fd38d' }}>✓</span>
          </Slam>
        </div>
      </AbsoluteFill>
      {atEnd ? <End f={f} /> : null}
      <Flare x={540} y={675} intensity={atEnd ? Math.max(0, 1 - (f - HIT.logo) / 10) : 0} color="255,240,225" />
      {void punch}
      {void easeInOut}
    </AbsoluteFill>
  );
};
