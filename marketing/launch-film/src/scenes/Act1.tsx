import React from 'react';
import { AbsoluteFill, Sequence, interpolate, useCurrentFrame, useVideoConfig } from 'remotion';
import { C, F } from '../kit/theme';
import { Camera, Caption, Grade, Vignette } from '../kit/lens';
import { Clock } from '../kit/props';
import { Portrait } from '../kit/portrait';
import { easeOut, fade, handheld, lerp, rand } from '../kit/motion';

// ============================================================================
// ACT 1 — Night one. Cold screen light, a restless hand-held camera.
// ============================================================================

/** The room behind every night-one shot: dark, lit only by a screen. */
const NightRoom: React.FC<{ glow?: number; children?: React.ReactNode }> = ({ glow = 1, children }) => (
  <AbsoluteFill style={{ background: C.night }}>
    <AbsoluteFill
      style={{
        background: `radial-gradient(ellipse 70% 55% at 50% 55%, rgba(120,170,220,${0.28 * glow}) 0%, rgba(20,30,45,0) 70%)`,
      }}
    />
    {children}
  </AbsoluteFill>
);

/** LCD sub-pixels, visible only in macro. */
const Subpixels: React.FC<{ opacity: number; pitch?: number }> = ({ opacity, pitch = 6 }) => (
  <AbsoluteFill
    style={{
      opacity,
      mixBlendMode: 'multiply',
      backgroundImage: `repeating-linear-gradient(90deg, rgba(255,60,60,0.9) 0 ${pitch / 3}px, rgba(60,255,90,0.9) ${pitch / 3}px ${(pitch * 2) / 3}px, rgba(70,90,255,0.9) ${(pitch * 2) / 3}px ${pitch}px), repeating-linear-gradient(0deg, rgba(0,0,0,0.5) 0 1px, transparent 1px ${pitch}px)`,
    }}
  />
);

// ---- 1. The hook: the rejection, in macro ---------------------------------
const Hook: React.FC = () => {
  const f = useCurrentFrame();
  const hh = handheld(f, 6, 2);
  const focus = lerp(f, [0, 16], [14, 0], easeOut);
  const pull = lerp(f, [0, 90], [1.55, 1.3]);
  const shake = f > 10 && f < 18 ? Math.sin(f * 3.1) * 10 : 0; // the beep hits
  return (
    <NightRoom>
      <Camera scale={pull} x={hh.x + shake} y={hh.y} rotate={hh.r - 2} blur={focus}>
        <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ width: 760, background: '#f4f6f8', padding: '40px 44px', boxShadow: '0 0 120px rgba(150,190,255,0.35)' }}>
            <div style={{ fontFamily: 'Arial, sans-serif', fontSize: 22, color: '#5c6670', marginBottom: 18 }}>Upload Photograph *</div>
            <div
              style={{
                fontFamily: 'Arial, sans-serif',
                fontSize: 30,
                fontWeight: 700,
                color: C.error,
                lineHeight: 1.25,
                borderLeft: `6px solid ${C.error}`,
                paddingLeft: 18,
              }}
            >
              Photo size should be between 10 KB and 200 KB.
            </div>
            <div style={{ fontFamily: 'Arial, sans-serif', fontSize: 20, color: '#8a939c', marginTop: 16 }}>
              Selected file: IMG_20261112_231402.jpg (3.4 MB)
            </div>
          </div>
        </AbsoluteFill>
        <Subpixels opacity={lerp(f, [0, 40], [0.5, 0.18])} />
      </Camera>
      <Grade tone="cold" />
    </NightRoom>
  );
};

// ---- 2. The clock and the calendar ----------------------------------------
const Calendar: React.FC<{ circle: number }> = ({ circle }) => {
  const days = Array.from({ length: 30 }, (_, i) => i + 1);
  return (
    <div style={{ width: 420, background: '#e9e4d6', boxShadow: '0 20px 40px rgba(0,0,0,0.5)' }}>
      <div style={{ height: 54, background: '#9c2f1f' }} />
      <div style={{ padding: '16px 22px 22px' }}>
        <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 44, color: '#2a2622' }}>NOVEMBER</div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(7, 1fr)', gap: 6, marginTop: 10 }}>
          {[...Array(6)].map((_, i) => <div key={`b${i}`} />)}
          {days.map((d) => (
            <div key={d} style={{ position: 'relative', fontFamily: F.body, fontWeight: 600, fontSize: 22, color: '#3a3530', textAlign: 'center' }}>
              {d}
              {d === 22 ? (
                <svg width="64" height="54" viewBox="0 0 64 54" style={{ position: 'absolute', left: -14, top: -14 }}>
                  <path
                    d="M8 30 C 4 12, 40 2, 56 18 C 66 34, 40 50, 20 46 C 6 42, 6 26, 16 18"
                    stroke="#c8261b"
                    strokeWidth={4}
                    fill="none"
                    strokeLinecap="round"
                    pathLength={1}
                    strokeDasharray={1}
                    strokeDashoffset={1 - circle}
                  />
                </svg>
              ) : null}
            </div>
          ))}
        </div>
        <div style={{ fontFamily: '"Segoe Print", "Comic Sans MS", cursive', fontSize: 24, color: '#c8261b', marginTop: 12, opacity: circle }}>
          JEE Main — last date!!
        </div>
      </div>
    </div>
  );
};

const WallClock: React.FC = () => {
  const f = useCurrentFrame();
  const hh = handheld(f, 5, 7);
  const dolly = lerp(f, [0, 90], [1.0, 1.08]);
  return (
    <NightRoom glow={0.7}>
      <AbsoluteFill style={{ background: '#151c24' }} />
      <AbsoluteFill style={{ background: 'radial-gradient(ellipse 60% 50% at 40% 80%, rgba(120,170,230,0.35), transparent 70%)' }} />
      <Camera scale={dolly} x={hh.x} y={hh.y} rotate={hh.r}>
        <div style={{ position: 'absolute', left: 90, top: 170 }}>
          <Clock minutes={23 * 60 + 14 + f / 30 / 60} size={480} face="#d9dde0" />
        </div>
        <div style={{ position: 'absolute', left: 560, top: 640, transform: 'rotate(2.5deg)' }}>
          <Calendar circle={lerp(f, [20, 60], [0, 1], easeOut)} />
        </div>
      </Camera>
      <Grade tone="cold" />
      <Caption text="11:14 PM. The form closes tonight." opacity={fade(f, 30, 10)} y={1170} />
    </NightRoom>
  );
};

// ---- 3. Tab chaos: the generic tools --------------------------------------
const TABS = [
  'Photo resizer online',
  'Compress JPG to 200KB',
  'Remove background free',
  'Resize to 413×531',
  'Signature resize',
  'Rename file online',
  'PDF compressor',
  'jee photo size??',
];

const GenericTool: React.FC<{ kind: 0 | 1 | 2; f: number }> = ({ kind, f }) => {
  // Deliberately the opposite of our system: rounded, gradient, ad-cluttered.
  const card: React.CSSProperties = {
    background: '#fff',
    borderRadius: 18,
    boxShadow: '0 8px 30px rgba(40,60,120,0.18)',
    padding: 28,
    fontFamily: 'Arial, sans-serif',
    color: '#2c3440',
  };
  if (kind === 0) {
    const typed = Math.max(0, Math.floor((f - 18) / 3));
    return (
      <div style={card}>
        <div style={{ fontSize: 22, color: '#6a7480' }}>Step 1: Select exam</div>
        <div style={{ marginTop: 10, padding: '14px 18px', borderRadius: 12, background: 'linear-gradient(90deg,#e8f0ff,#f4ecff)', fontSize: 28, fontWeight: 700 }}>
          JEE Main ✓
        </div>
        <div style={{ fontSize: 22, color: '#6a7480', marginTop: 24 }}>Step 2: Enter dimensions</div>
        <div style={{ display: 'flex', gap: 14, marginTop: 10 }}>
          {['Width (px)', 'Height (px)', 'Max KB'].map((p, i) => (
            <div key={p} style={{ flex: 1, padding: '14px 16px', border: '2px solid #c9d3e0', borderRadius: 12, fontSize: 22, color: i === 0 && typed ? '#2c3440' : '#9aa4b0' }}>
              {i === 0 && typed ? '413'.slice(0, typed) : p}
            </div>
          ))}
        </div>
        <div style={{ marginTop: 22, padding: '16px', borderRadius: 999, background: 'linear-gradient(90deg,#5b6cff,#a35bff)', color: '#fff', textAlign: 'center', fontSize: 24, fontWeight: 700 }}>
          Resize Now
        </div>
      </div>
    );
  }
  if (kind === 1) {
    const kb = Math.round(interpolate(f, [10, 40], [312, 198], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }));
    return (
      <div style={card}>
        <div style={{ display: 'flex', gap: 22, alignItems: 'center' }}>
          <Portrait variant="source" width={210} height={270} style={{ borderRadius: 12, filter: `blur(${interpolate(f, [10, 40], [0, 4.5], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' })}px) saturate(0.8)` }} />
          <div>
            <div style={{ fontSize: 22, color: '#6a7480' }}>Compressed!</div>
            <div style={{ fontSize: 64, fontWeight: 800, color: kb <= 200 ? '#1e9b52' : '#2c3440' }}>{kb} KB</div>
            <div style={{ fontSize: 20, color: '#9aa4b0' }}>Quality: 12%</div>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div style={{ ...card, position: 'relative', overflow: 'hidden' }}>
      <div style={{ display: 'flex', gap: 22, alignItems: 'center' }}>
        <div style={{ position: 'relative' }}>
          <Portrait variant="source" width={210} height={270} whiten={0.85} style={{ borderRadius: 12 }} />
          <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', transform: 'rotate(-30deg)', fontSize: 34, fontWeight: 900, color: 'rgba(90,100,255,0.55)', letterSpacing: 2 }}>
            WATERMARK
          </div>
        </div>
        <div>
          <div style={{ fontSize: 24, fontWeight: 700 }}>Background removed</div>
          <div style={{ marginTop: 16, padding: '14px 22px', borderRadius: 999, background: 'linear-gradient(90deg,#ff7a59,#ff3d8b)', color: '#fff', fontSize: 22, fontWeight: 700 }}>
            Download HD — Sign up
          </div>
        </div>
      </div>
    </div>
  );
};

const TabChaos: React.FC = () => {
  const f = useCurrentFrame();
  const hh = handheld(f, 7, 11);
  const tabsShown = Math.min(TABS.length, 1 + Math.floor(f / 22));
  const pane: 0 | 1 | 2 = f < 80 ? 0 : f < 160 ? 1 : 2;
  const local = pane === 0 ? f : pane === 1 ? f - 80 : f - 160;
  const caps = ['Picked the exam. Still had to resize it yourself.', 'Under 200 KB. Also unreadable.', 'Background fixed. Watermark added.'];
  const punch = 1 + Math.max(0, 0.04 - local * 0.004); // a tiny push on every cut
  return (
    <NightRoom>
      <Camera scale={1.06 * punch} x={hh.x} y={hh.y} rotate={hh.r - 1}>
        <AbsoluteFill style={{ padding: '120px 50px 0' }}>
          <div style={{ background: '#dfe3e8', borderRadius: '14px 14px 0 0', height: 1000, boxShadow: '0 0 140px rgba(140,180,255,0.3)', overflow: 'hidden' }}>
            <div style={{ display: 'flex', gap: 4, padding: '12px 12px 0', background: '#c8ced6' }}>
              {TABS.slice(0, tabsShown).map((t, i) => (
                <div
                  key={t}
                  style={{
                    flex: '1 1 0',
                    minWidth: 0,
                    padding: '12px 12px',
                    background: i === tabsShown - 1 ? '#eef1f4' : '#b6bec8',
                    borderRadius: '10px 10px 0 0',
                    fontFamily: 'Arial, sans-serif',
                    fontSize: 15,
                    color: '#333',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                  }}
                >
                  {t}
                </div>
              ))}
            </div>
            <div style={{ padding: '18px 22px', background: '#eef1f4', fontFamily: 'Arial, sans-serif', fontSize: 17, color: '#7a838e' }}>
              🔒 free-online-image-tool.example/{['resize', 'compress', 'remove-bg'][pane]}
            </div>
            <div style={{ padding: 36, background: 'linear-gradient(160deg,#f6f8ff,#fbf3ff)', height: '100%' }}>
              {/* the ad slot every one of these sites has */}
              <div style={{ height: 110, borderRadius: 12, background: 'repeating-linear-gradient(45deg,#ffe9a8 0 20px,#ffdf80 20px 40px)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontFamily: 'Arial', fontWeight: 800, fontSize: 26, color: '#7a5a00', marginBottom: 28 }}>
                AD · Download Now ▶
              </div>
              <GenericTool kind={pane} f={local} />
            </div>
          </div>
        </AbsoluteFill>
      </Camera>
      <Grade tone="cold" />
      <Vignette strength={0.7} />
      <Caption text={caps[pane]} opacity={fade(local, 8, 6, 70, 6)} y={1180} />
    </NightRoom>
  );
};

// ---- 4. The portal says no: face coverage ----------------------------------
const PortalFrame: React.FC<{ title: string; children: React.ReactNode }> = ({ title, children }) => (
  <div style={{ width: 900, background: '#f7f8fa', boxShadow: '0 0 140px rgba(140,180,255,0.3)' }}>
    <div style={{ background: '#1f3a68', color: '#fff', padding: '18px 26px', fontFamily: 'Arial', fontSize: 22, fontWeight: 700 }}>
      Application Form · Step 3 of 5 · Upload Documents
    </div>
    <div style={{ padding: 30, fontFamily: 'Arial' }}>
      <div style={{ fontSize: 22, color: '#5c6670', marginBottom: 18 }}>{title}</div>
      {children}
    </div>
  </div>
);

const Coverage: React.FC = () => {
  const f = useCurrentFrame();
  const hh = handheld(f, 6, 21);
  // her manual crop, wrong twice
  const cropW = interpolate(f, [0, 30, 45, 70], [300, 230, 260, 210], { extrapolateRight: 'clamp' });
  return (
    <NightRoom>
      <Camera scale={lerp(f, [0, 90], [1.0, 1.12])} x={hh.x} y={hh.y} rotate={hh.r}>
        <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
          <PortalFrame title="Photograph (crop to face)">
            <div style={{ display: 'flex', gap: 30 }}>
              <div style={{ position: 'relative' }}>
                <Portrait variant="source" width={300} height={380} />
                <div style={{ position: 'absolute', left: (300 - cropW) / 2, top: 30, width: cropW, height: cropW * 1.28, border: '3px dashed #ffd400', boxShadow: '0 0 0 999px rgba(0,0,0,0.45)' }} />
              </div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: C.error, borderLeft: `6px solid ${C.error}`, paddingLeft: 16, opacity: f > 50 ? 1 : 0 }}>
                  Photo rejected: face must cover 80% of the frame.
                </div>
                <div style={{ fontSize: 20, color: '#8a939c', marginTop: 14, opacity: f > 50 ? 1 : 0 }}>Attempt 4</div>
              </div>
            </div>
          </PortalFrame>
        </AbsoluteFill>
      </Camera>
      <Grade tone="cold" />
      <Vignette strength={0.7} />
      <Caption text="Nobody tells you how much is 80%." opacity={fade(f, 55, 8)} />
    </NightRoom>
  );
};

// ---- 5. The signature under a yellow bulb ----------------------------------
const Signature: React.FC = () => {
  const f = useCurrentFrame();
  const hh = handheld(f, 5, 31);
  const draw = lerp(f, [0, 40], [0, 1], easeOut);
  return (
    <NightRoom>
      <Camera scale={lerp(f, [0, 90], [1.15, 1.0])} x={hh.x} y={hh.y} rotate={hh.r + 3}>
        <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
          {/* a phone photo of a signature: grey paper, a hand's shadow, a yellow cast */}
          <div style={{ width: 860, height: 520, position: 'relative', background: 'linear-gradient(115deg,#b9ad8c 0%,#d8cfb4 45%,#8e8670 100%)', boxShadow: '0 30px 60px rgba(0,0,0,0.6)' }}>
            <div style={{ position: 'absolute', right: -60, top: -40, width: 520, height: 420, background: 'radial-gradient(ellipse at 70% 30%, rgba(30,24,15,0.55), transparent 65%)' }} />
            <svg width="860" height="520" viewBox="0 0 860 520" style={{ position: 'absolute' }}>
              <path
                d="M140 320 C 180 200, 230 200, 220 300 C 214 360, 260 250, 300 260 C 340 270, 320 330, 360 300 C 400 270, 420 220, 450 290 C 470 340, 520 240, 560 270 C 600 300, 640 260, 700 250"
                stroke="#1c2a6a"
                strokeWidth={5}
                fill="none"
                strokeLinecap="round"
                pathLength={1}
                strokeDasharray={1}
                strokeDashoffset={1 - draw}
                opacity={0.75}
              />
            </svg>
          </div>
        </AbsoluteFill>
      </Camera>
      <Grade tone="cold" amount={0.6} />
      <div style={{ position: 'absolute', left: 110, top: 1010, fontFamily: 'Arial', fontSize: 28, fontWeight: 700, color: '#ff6b6b', opacity: f > 50 ? 1 : 0 }}>
        ✕ Signature not clear. Upload again.
      </div>
      <Vignette strength={0.7} />
    </NightRoom>
  );
};

// ---- 6. The filename -------------------------------------------------------
const NAMES = ['IMG_20261112_234501.jpg', 'jee photo.jpg', 'jee photo final.jpg', 'jee photo final FINAL.jpg'];
const Filename: React.FC = () => {
  const f = useCurrentFrame();
  const hh = handheld(f, 4, 41);
  const idx = Math.min(NAMES.length - 1, Math.floor(f / 20));
  const local = f - idx * 20;
  const name = NAMES[idx];
  const shown = idx === 0 ? name : name.slice(0, Math.min(name.length, 4 + local * 2));
  return (
    <NightRoom>
      <Camera scale={2.1} x={hh.x} y={hh.y} rotate={hh.r - 2} blur={f < 6 ? 6 - f : 0}>
        <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ background: '#f4f6f8', padding: '22px 28px', fontFamily: 'Consolas, monospace', fontSize: 30, color: '#22282f', boxShadow: '0 0 90px rgba(140,180,255,0.35)', minWidth: 460 }}>
            {shown}
            <span style={{ opacity: Math.floor(f / 8) % 2 ? 1 : 0 }}>▏</span>
          </div>
        </AbsoluteFill>
        <Subpixels opacity={0.14} pitch={5} />
      </Camera>
      <Grade tone="cold" />
      <div style={{ position: 'absolute', left: 0, right: 0, top: 860, textAlign: 'center', fontFamily: 'Arial', fontSize: 30, fontWeight: 700, color: '#ff6b6b', opacity: f > 68 ? 1 : 0 }}>
        ✕ Invalid file name format.
      </div>
      <Vignette strength={0.75} />
    </NightRoom>
  );
};

// ---- 7–8. 2:40 AM, and the cost -------------------------------------------
const LateClock: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <NightRoom glow={0.4}>
      <AbsoluteFill style={{ background: '#10151b' }} />
      <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
        <Camera scale={lerp(f, [0, 60], [1.0, 1.05])}>
          <AbsoluteFill style={{ alignItems: 'center', justifyContent: 'center' }}>
            <Clock minutes={2 * 60 + 40} size={600} face="#c9ced3" />
          </AbsoluteFill>
        </Camera>
      </AbsoluteFill>
      <Grade tone="cold" />
      <Vignette strength={0.8} />
      <Caption text="2:40 AM." opacity={fade(f, 8, 6)} y={1170} size={58} />
    </NightRoom>
  );
};

const DustMotes: React.FC<{ f: number }> = ({ f }) => (
  <>
    {Array.from({ length: 36 }, (_, i) => {
      const x = rand(i) * 700 + 180;
      const y = ((rand(i + 50) * 700 + f * (0.3 + rand(i + 9) * 0.5)) % 700) + 200;
      const s = 2 + rand(i + 3) * 4;
      return <div key={i} style={{ position: 'absolute', left: x + Math.sin(f / 20 + i) * 8, top: y, width: s, height: s, borderRadius: 99, background: 'rgba(255,230,190,0.55)', filter: 'blur(1px)' }} />;
    })}
  </>
);

/** The book that never got opened. Title kept generic. */
export const Book: React.FC<{ open?: number; dusty?: boolean }> = ({ open = 0, dusty }) => (
  <div style={{ position: 'relative', width: 520, height: 680 }}>
    <div style={{ position: 'absolute', inset: 0, background: '#1d3f5e', boxShadow: '0 40px 70px rgba(0,0,0,0.6)', border: '4px solid #142c43' }}>
      <div style={{ position: 'absolute', left: 50, right: 50, top: 80, borderTop: '3px solid #e9d9b0', borderBottom: '3px solid #e9d9b0', padding: '22px 0', textAlign: 'center' }}>
        <div style={{ fontFamily: F.display, fontWeight: 900, fontSize: 92, color: '#e9d9b0', lineHeight: 0.9 }}>PHYSICS</div>
        <div style={{ fontFamily: F.body, fontWeight: 600, fontSize: 26, color: '#c9b98f', marginTop: 10, letterSpacing: '0.2em' }}>CONCEPTS · VOL. 1</div>
      </div>
      {dusty ? <div style={{ position: 'absolute', inset: 0, background: 'radial-gradient(ellipse at 40% 40%, rgba(220,210,190,0.18), transparent 70%)' }} /> : null}
    </div>
    {open > 0 ? (
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background: '#f3ecd9',
          transformOrigin: 'left center',
          transform: `perspective(1600px) rotateY(${-open * 165}deg)`,
          backfaceVisibility: 'hidden',
          border: '4px solid #142c43',
        }}
      />
    ) : null}
  </div>
);

const TheCost: React.FC = () => {
  const f = useCurrentFrame();
  const { fps } = useVideoConfig();
  const push = lerp(f, [0, 150], [1.0, 1.14]);
  return (
    <AbsoluteFill style={{ background: '#0a0c0f' }}>
      <Camera scale={push} y={lerp(f, [0, 150], [0, -20])}>
        {/* the desk, top-down, the lamp switched off, the laptop still glowing at the edge */}
        <AbsoluteFill style={{ background: 'radial-gradient(ellipse 60% 55% at 45% 45%, #2a2420 0%, #0c0b0a 75%)' }} />
        <div style={{ position: 'absolute', right: -120, top: 260, width: 360, height: 620, background: 'linear-gradient(90deg, rgba(120,170,230,0.0), rgba(120,170,230,0.35))', filter: 'blur(30px)' }} />
        <div style={{ position: 'absolute', left: 230, top: 320, transform: 'rotate(-6deg)' }}>
          <Book dusty />
        </div>
        <DustMotes f={f} />
      </Camera>
      <Grade tone="cold" amount={0.7} />
      <Vignette strength={0.85} />
      <div style={{ position: 'absolute', left: 0, right: 0, top: 140, textAlign: 'center', opacity: fade(f, 10, 12, 70, 10) }}>
        <div style={{ fontFamily: F.hindi, fontWeight: 500, fontSize: 50, color: '#e8e2d4' }}>“बेटा, सो जाओ…”</div>
        <div style={{ fontFamily: F.body, fontSize: 28, color: '#a9a294', marginTop: 8 }}>Go to sleep, beta…</div>
      </div>
      <Caption text="Every year, lakhs of students lose a night like this." opacity={fade(f, 84, 14)} y={1120} size={50} />
      {void fps}
    </AbsoluteFill>
  );
};

// ---- Act 1 timeline (frames, 30 fps) --------------------------------------
export const ACT1 = 900;
export const Act1: React.FC = () => (
  <AbsoluteFill>
    <Sequence durationInFrames={90}><Hook /></Sequence>
    <Sequence from={90} durationInFrames={90}><WallClock /></Sequence>
    <Sequence from={180} durationInFrames={240}><TabChaos /></Sequence>
    <Sequence from={420} durationInFrames={90}><Coverage /></Sequence>
    <Sequence from={510} durationInFrames={90}><Signature /></Sequence>
    <Sequence from={600} durationInFrames={90}><Filename /></Sequence>
    <Sequence from={690} durationInFrames={60}><LateClock /></Sequence>
    <Sequence from={750} durationInFrames={150}><TheCost /></Sequence>
  </AbsoluteFill>
);
