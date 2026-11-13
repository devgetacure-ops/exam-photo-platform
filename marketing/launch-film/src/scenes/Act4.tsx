import React from 'react';
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame } from 'remotion';
import { C, F } from '../kit/theme';
import { Camera, Caption, Grade, PaperTexture, Vignette } from '../kit/lens';
import { Wordmark } from '../kit/props';
import { Book } from './Act1';
import { easeInOut, easeOut, fade, lerp } from '../kit/motion';

// ============================================================================
// ACT 4 — What she got back. Then the name.
// ============================================================================

const Study: React.FC = () => {
  const f = useCurrentFrame();
  // 0–120 the book opens under the lamp; 120–270 the night passes; 270–330 dawn, lamp off
  const open = lerp(f, [10, 60], [0, 1], easeInOut);
  const night = lerp(f, [120, 260], [0, 1], easeInOut);
  const lampOff = lerp(f, [282, 292], [0, 1], easeOut);
  const dawn = lerp(f, [230, 330], [0, 1], easeInOut);
  const lines = Math.floor(interpolate(f, [70, 260], [0, 14], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }));
  return (
    <AbsoluteFill style={{ background: '#1d1712' }}>
      <Camera scale={lerp(f, [0, 330], [1.12, 1.0])} y={lerp(f, [0, 330], [-30, 0])}>
        {/* the desk, the lamp pool moving as the night turns */}
        <AbsoluteFill style={{ background: `radial-gradient(ellipse 70% 60% at ${40 + night * 10}% ${30 + night * 5}%, rgba(255,190,110,${0.6 * (1 - lampOff)}) 0%, rgba(40,28,18,0) 70%)` }} />
        <AbsoluteFill style={{ background: `linear-gradient(200deg, rgba(200,220,255,${0.45 * dawn}) 0%, rgba(255,226,190,${0.35 * dawn}) 50%, rgba(0,0,0,0) 90%)` }} />
        <div style={{ position: 'absolute', left: 120, top: 330, transform: 'rotate(-4deg)' }}>
          <div style={{ position: 'relative' }}>
            <Book open={open} />
            {/* the right-hand page */}
            <div style={{ position: 'absolute', left: 0, top: 0, width: 520, height: 680, background: '#f3ecd9', opacity: open > 0.5 ? 1 : 0, border: '4px solid #142c43', padding: 40 }}>
              {[...Array(9)].map((_, i) => <div key={i} style={{ height: 6, background: '#c9bfa6', marginTop: 26, width: `${60 + ((i * 37) % 35)}%` }} />)}
            </div>
          </div>
        </div>
        {/* her notebook filling up */}
        <div style={{ position: 'absolute', left: 640, top: 520, width: 360, height: 480, background: '#fdfbf4', transform: 'rotate(6deg)', boxShadow: '0 20px 40px rgba(0,0,0,0.4)', padding: 26 }}>
          {[...Array(lines)].map((_, i) => (
            <div key={i} style={{ height: 4, background: i % 5 === 4 ? C.signal : '#2b3a6b', marginTop: 24, width: `${40 + ((i * 53) % 55)}%`, opacity: 0.8 }} />
          ))}
        </div>
        {/* tea, emptying */}
        <div style={{ position: 'absolute', left: 790, top: 250, width: 140, height: 140, borderRadius: 999, background: '#e8e0d0', border: '10px solid #cfc4ae' }}>
          <div style={{ position: 'absolute', inset: 12 + night * 30, borderRadius: 999, background: '#8a5a2b', opacity: 1 - night * 0.9 }} />
        </div>
      </Camera>
      <Grade tone="warm" amount={1 - dawn} />
      <Grade tone="dawn" amount={dawn} />
      <Vignette strength={0.55 - dawn * 0.25} />
      <Caption text="The form was never the exam." opacity={fade(f, 30, 12, 110, 10)} y={1150} size={52} />
      <Caption text="Spend tonight on what is." opacity={fade(f, 140, 12, 230, 10)} y={1150} size={52} />
      <Caption text="You prepare for the exam. We'll prepare the files." opacity={fade(f, 250, 12)} y={1120} size={46} />
    </AbsoluteFill>
  );
};

const SCRIPTS: { t: string; font: keyof typeof F }[] = [
  { t: 'বাংলা', font: 'bangla' },
  { t: 'தமிழ்', font: 'tamil' },
  { t: 'తెలుగు', font: 'telugu' },
  { t: 'मराठी', font: 'hindi' },
  { t: 'ગુજરાતી', font: 'gujarati' },
  { t: 'ਪੰਜਾਬੀ', font: 'gurmukhi' },
  { t: 'ଓଡ଼ିଆ', font: 'odia' },
  { t: 'ಕನ್ನಡ', font: 'kannada' },
  { t: 'മലയാളം', font: 'malayalam' },
];

const EndCard: React.FC = () => {
  const f = useCurrentFrame();
  const reveal = interpolate(f, [6, 40], [0, 13], { easing: easeOut, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  const toHindi = lerp(f, [120, 132], [0, 1], easeInOut);
  return (
    <AbsoluteFill style={{ background: C.paper }}>
      <PaperTexture opacity={0.4} seed={31} />
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 50, paddingBottom: 120 }}>
        <Wordmark cell={96} reveal={reveal} />
        <div style={{ position: 'relative', height: 260, width: 940 }}>
          {/* English, then the same line in Hindi */}
          <div style={{ position: 'absolute', inset: 0, opacity: 1 - toHindi, transform: `translateY(${-toHindi * 20}px)` }}>
            <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 112, lineHeight: 0.86, color: C.ink, textAlign: 'center', opacity: fade(f, 40, 10) }}>
              PICK YOUR EXAM.
              <br />
              <span style={{ display: 'inline-block', marginTop: 18, background: C.signal, color: C.paper, padding: '12px 20px 0' }}>GET THE WHOLE KIT.</span>
            </div>
          </div>
          <div style={{ position: 'absolute', inset: 0, opacity: toHindi, transform: `translateY(${(1 - toHindi) * 20}px)`, textAlign: 'center' }}>
            <div style={{ fontFamily: F.hindi, fontWeight: 700, fontSize: 92, lineHeight: 1.15, color: C.ink }}>
              परीक्षा चुनिए।
              <br />
              <span style={{ background: C.signal, color: C.paper, padding: '0 20px' }}>पूरी किट पाइए।</span>
            </div>
          </div>
        </div>
        <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 30, color: C.ink55, opacity: fade(f, 150, 10) }}>
          Now in Hindi. More Indian languages coming soon.
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '10px 26px', width: 900 }}>
          {SCRIPTS.map((s, i) => (
            <div key={s.t} style={{ fontFamily: F[s.font], fontWeight: 600, fontSize: 40, color: C.ink40, opacity: fade(f, 160 + i * 5, 8) * 0.9 }}>
              {s.t}
            </div>
          ))}
        </div>
      </AbsoluteFill>
      <div style={{ position: 'absolute', left: 0, right: 0, bottom: 110, textAlign: 'center', opacity: fade(f, 60, 10) }}>
        <span style={{ fontFamily: F.display, fontWeight: 900, fontSize: 64, color: C.paper, background: C.ink, padding: '14px 30px 4px', boxShadow: `7px 7px 0 ${C.signal}` }}>
          EXAMUPLOADKIT.COM
        </span>
        <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 28, color: C.ink55, marginTop: 26 }}>Free. No login.</div>
      </div>
    </AbsoluteFill>
  );
};

export const ACT4 = 600;
export const Act4: React.FC = () => (
  <AbsoluteFill>
    <Sequence durationInFrames={330}><Study /></Sequence>
    <Sequence from={330} durationInFrames={270}><EndCard /></Sequence>
  </AbsoluteFill>
);
void Vignette;
