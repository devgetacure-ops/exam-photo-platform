import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { C, F } from '../kit/theme';
import { easeIn, easeInOut, easeOut, fade, lerp } from '../kit/motion';
import { Wordmark } from '../kit/props';
import { LivePage } from '../kit/screen';
import { Beam, Dust, Flare, HIT, Rect, Slam, Studio, mixRect, punch, shake } from './cinema';
import { Phone3D } from './phone3d';

// ============================================================================
// THE TURN — the line becomes our search, "JEE", and the drop into the phone.
// ============================================================================

const RS: Rect = { x: 110, y: 600, w: 860, h: 132 }; // the search field
const ROW_H = 118;
const RR: Rect = { x: 110, y: RS.y + RS.h + 26, w: 860, h: ROW_H }; // the JEE (MAIN) result
// the phone's screen, at rest
export const PHONE = { x: 560, y: 220, w: 410 };
const PH = PHONE.w * (844 / 390);
const RP: Rect = { x: PHONE.x, y: PHONE.y, w: PHONE.w, h: PH };

const RESULTS = [
  { n: 'JEE (MAIN) 2027', b: 'National Testing Agency · 6 files' },
  { n: 'JEE (ADVANCED) 2027', b: 'IIT · 7 files' },
  { n: 'NCHM JEE 2027', b: 'National Testing Agency' },
];

const Search: React.FC<{ f: number }> = ({ f }) => {
  // the flare line opens into the field's two edges
  const open = lerp(f, [405, 418], [0, 1], easeOut);
  const r: Rect = { x: 540 - (RS.w / 2) * Math.min(1, 0.2 + open), y: RS.y + RS.h / 2 - (RS.h / 2) * open, w: RS.w * Math.min(1, 0.2 + open), h: Math.max(4, RS.h * open) };
  const typed = f < 435 ? '' : f < 442 ? 'J' : f < 450 ? 'JE' : 'JEE';
  const reveal = lerp(f, [452, 476], [0, 13], easeOut);
  const pick = f >= 472;
  const tap = lerp(f, [474, 480], [0, 1]);
  return (
    <>
      <div style={{ position: 'absolute', left: 110, top: 380, opacity: f > 450 ? 1 : 0 }}>
        <Wordmark cell={100} reveal={reveal} color={C.paper} bg="transparent" />
      </div>
      <div style={{ position: 'absolute', left: r.x, top: r.y, width: r.w, height: r.h, background: C.paper, border: `4px solid ${C.paper}`, boxShadow: open > 0.9 ? `10px 10px 0 ${C.signal}` : undefined, overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 22, height: '100%', padding: '0 32px', opacity: open > 0.9 ? 1 : 0 }}>
          <svg width="44" height="44" viewBox="0 0 24 24"><circle cx="10" cy="10" r="7" stroke={C.ink} strokeWidth="2.6" fill="none" /><line x1="15" y1="15" x2="21" y2="21" stroke={C.ink} strokeWidth="2.6" /></svg>
          <span style={{ fontFamily: F.display, fontWeight: 900, fontSize: 70, color: typed ? C.ink : C.ink40, lineHeight: 1 }}>{typed || 'Search your exam'}</span>
          <span style={{ width: 5, height: 64, background: C.signal, opacity: Math.floor(f / 6) % 2 || typed ? 1 : 0 }} />
        </div>
      </div>
      {RESULTS.map((res, i) => {
        const v = lerp(f, [450 + i * 3, 458 + i * 3], [0, 1], easeOut);
        const hot = i === 0 && pick;
        return (
          <div
            key={res.n}
            style={{
              position: 'absolute', left: RR.x, top: RR.y + i * (ROW_H + 14), width: RR.w, height: ROW_H, opacity: i === 0 ? v : v * (1 - tap),
              transform: `translateY(${(1 - v) * -30}px)`, background: hot ? C.signal : C.paper, border: `4px solid ${C.paper}`,
              display: 'flex', flexDirection: 'column', justifyContent: 'center', padding: '0 32px',
            }}
          >
            <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 58, lineHeight: 0.9, color: C.ink }}>{res.n}</div>
            <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 24, color: hot ? C.ink : C.ink55, marginTop: 6 }}>{res.b}</div>
          </div>
        );
      })}
      <div style={{ position: 'absolute', left: 110, top: 1180, opacity: fade(f, 458, 6) * (1 - tap) }}>
        <Slam font={F.display} size={58} color={C.paper}>770+ exams. Each with its own rules.</Slam>
      </div>
      {/* the tap */}
      {f >= 474 && f < 482 ? <div style={{ position: 'absolute', left: 540 - 30 - tap * 50, top: RR.y + ROW_H / 2 - 30 - tap * 50, width: 60 + tap * 100, height: 60 + tap * 100, borderRadius: 999, border: `5px solid ${C.ink}`, opacity: 1 - tap }} /> : null}
    </>
  );
};

/** The drop: the picked result becomes the phone's screen, and the phone forms around it. */
const PhoneShot: React.FC<{ f: number }> = ({ f }) => {
  const form = lerp(f, [HIT.drop, HIT.drop + 12], [0, 1], easeOut);
  const settle = lerp(f, [HIT.drop + 6, HIT.drop + 60], [0, 1], easeOut);
  const scr = form < 1 ? mixRect(RR, RP, form) : RP;
  // scroll the real page on the click beats: top → the answer → the six files
  const scroll = f < HIT.click[0] ? 0 : f < HIT.click[1] ? lerp(f, [HIT.click[0], HIT.click[0] + 14], [0, 300], easeInOut) : lerp(f, [HIT.click[1], HIT.click[1] + 14], [300, 747], easeInOut);
  // the dive into the photograph row's icon
  const dive = lerp(f, [HIT.click[3], 630], [0, 1], easeIn);
  const s = PHONE.w / 390;
  const topH = 270 * (PHONE.w / 1170);
  const iconX = PHONE.x + 46 * s;
  const iconY = PHONE.y + topH + (857 - 747) * s;
  const ry = lerp(f, [HIT.drop, 590], [-24, -8], easeOut) * (1 - lerp(f, [585, 600], [0, 1], easeInOut));
  const rx = 6 * (1 - lerp(f, [585, 600], [0, 1]));
  const row = f >= HIT.click[2];
  const sh = shake(f, 16);
  const zoom = 1 + Math.pow(dive, 3) * 34;
  const lines: [number, string, string][] = [
    [HIT.click[0], 'One exam.', C.paper],
    [HIT.click[1], 'Every file', C.paper],
    [HIT.click[1] + 6, 'it asks for.', C.paper],
    [HIT.click[2], 'One click.', C.signal],
  ];
  return (
    <AbsoluteFill style={{ transform: `translate(${sh.x}px, ${sh.y}px) scale(${zoom})`, transformOrigin: `${iconX}px ${iconY}px`, filter: dive > 0.1 ? `blur(${dive * 6}px)` : undefined }}>
      <div style={{ position: 'absolute', left: 0, top: 0, perspective: 2200, perspectiveOrigin: `${PHONE.x + PHONE.w / 2}px 675px`, width: 1080, height: 1350 }}>
        <div style={{ position: 'absolute', left: scr.x - (PHONE.w * 0.04) * form, top: scr.y - (PHONE.w * 0.04) * form, transformStyle: 'preserve-3d' }}>
          <Phone3D w={scr.w} ry={ry * form} rx={rx * form} bezel={form} glare={lerp(f, [HIT.drop, 630], [0.0, 1.1])}>
            <div style={{ position: 'absolute', inset: 0, height: scr.h }}>
              <LivePage page="jee" width={scr.w} scroll={scroll} />
              {/* the photograph row, called out */}
              <div style={{ position: 'absolute', left: 12 * s, top: topH + (835 - scroll) * s, width: 366 * s, height: 46 * s, border: `${3 * s}px solid ${C.signal}`, opacity: row ? 1 : 0 }} />
            </div>
          </Phone3D>
        </div>
      </div>
      {/* the words, on the click beats */}
      <div style={{ position: 'absolute', left: 64, top: 300, width: 470, opacity: 1 - dive * 2 }}>
        {lines.map(([at, t, c]) => {
          const v = lerp(f, [at, at + 5], [0, 1], easeOut);
          return (
            <div key={t} style={{ opacity: f >= at ? 1 : 0, transform: `translateY(${(1 - v) * 24}px)` }}>
              <Slam font={F.display} size={104} color={c} split={Math.max(0, 1 - (f - at) / 5) * 0.6}>
                {t}
              </Slam>
            </div>
          );
        })}
        <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 28, color: '#bdb6a8', marginTop: 34, opacity: fade(f, HIT.click[2] + 4, 6) }}>
          Read from the exam's own bulletin. Updated as its rules change.
        </div>
      </div>
      <Flare x={PHONE.x + PHONE.w / 2} y={PHONE.y} intensity={Math.max(0, 1 - (f - HIT.drop) / 10) * (f >= HIT.drop ? 1 : 0)} />
      {void settle}
    </AbsoluteFill>
  );
};

export const Turn: React.FC = () => {
  const f = useCurrentFrame();
  const drop = f >= HIT.drop;
  return (
    <AbsoluteFill>
      <Studio warmth={drop ? 1.2 : 0.6} tone="#060606" />
      {drop ? <Beam x={260} y={-80} angle={-24} opacity={0.12} /> : null}
      <Dust count={50} opacity={0.4} seed={5} />
      {f < HIT.drop ? <Search f={f} /> : <PhoneShot f={f} />}
      {f >= 405 && f < 412 ? <Flare x={540} y={RS.y + RS.h / 2} intensity={1 - (f - 405) / 7} color="255,240,225" /> : null}
      {void punch}
      {void easeInOut}
    </AbsoluteFill>
  );
};
