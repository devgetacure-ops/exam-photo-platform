import React from 'react';
import { AbsoluteFill, Audio, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';
import { C } from '../kit/theme';
import { easeOut, lerp } from '../kit/motion';
import { Dust, FilmFinish, HIT, Studio } from './cinema';
import { Problem } from './problem';
import { Turn } from './turn';
import { Engine } from './engine';
import { Finale } from './finale';

// THE FRAME — 50 seconds, cut to the score's own hits.
export const FRAME_TOTAL = HIT.end;

/** The scenes alone, at the master's 1080 × 1350, with no finish and no sound. */
const Scenes: React.FC = () => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ background: '#000', overflow: 'hidden' }}>
      {f < 408 ? <Problem /> : null}
      {f >= 405 && f < 632 ? <Turn /> : null}
      {f >= 628 && f < 1042 ? <Engine /> : null}
      {f >= 1020 ? <Finale /> : null}
    </AbsoluteFill>
  );
};

const Score: React.FC = () => (
  // this score plays on to 50 s, so it is eased out over the final frames
  <Audio src={staticFile('audio/music.wav')} volume={(t) => (t > FRAME_TOTAL - 20 ? Math.max(0, (FRAME_TOTAL - t) / 20) : 1)} />
);

/** The 4:5 master. */
export const TheFrame: React.FC = () => (
  <AbsoluteFill style={{ background: '#000' }}>
    <Scenes />
    <FilmFinish />
    <Score />
  </AbsoluteFill>
);

/**
 * The same film on another canvas (9:16, 16:9). The 4:5 picture is fitted
 * whole -- nothing is cropped out of it -- and the studio carries on into the
 * extra space, turning to paper with the end card, so the bands read as more of
 * the same set rather than as letterboxing. Grain, vignette and the hit flashes
 * are laid over the whole canvas, so there is no seam where the picture ends.
 */
export const Reframed: React.FC = () => {
  const f = useCurrentFrame();
  const { width, height } = useVideoConfig();
  const scale = Math.min(width / 1080, height / 1350);
  const w = 1080 * scale;
  const h = 1350 * scale;
  // the same timing and easing as the end card's own paper, so the bands keep pace with it
  const paper = lerp(f, [HIT.logo + 6, HIT.logo + 10], [0, 1], easeOut); // as the end card's white frame reaches the picture's edges
  // feather the picture into the bands, so its edge is never a line
  const feather = 60 * scale;
  const mask = width > w
    ? `linear-gradient(90deg, transparent 0, #000 ${feather}px, #000 calc(100% - ${feather}px), transparent 100%)`
    : `linear-gradient(180deg, transparent 0, #000 ${feather}px, #000 calc(100% - ${feather}px), transparent 100%)`;
  return (
    <AbsoluteFill style={{ background: '#050505' }}>
      <Studio warmth={1} tone="#050505" />
      <Dust count={90} opacity={0.35} seed={21} />
      <AbsoluteFill style={{ background: C.paper, opacity: paper }} />
      <div
        style={{
          position: 'absolute',
          left: (width - w) / 2,
          top: (height - h) / 2,
          width: w,
          height: h,
          WebkitMaskImage: f < HIT.logo + 6 ? mask : undefined,
          maskImage: f < HIT.logo + 6 ? mask : undefined,
        }}
      >
        <div style={{ width: 1080, height: 1350, transform: `scale(${scale})`, transformOrigin: '0 0', position: 'relative' }}>
          <Scenes />
        </div>
      </div>
      <FilmFinish />
      <Score />
    </AbsoluteFill>
  );
};
