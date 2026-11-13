import React from 'react';
import { AbsoluteFill, Audio, Sequence, getStaticFiles, interpolate, staticFile, useCurrentFrame } from 'remotion';
import { Act1, ACT1 } from './scenes/Act1';
import { Act2, ACT2 } from './scenes/Act2';
import { Act3, ACT3 } from './scenes/Act3';
import { Act4, ACT4 } from './scenes/Act4';
import { Grain } from './kit/lens';

export const TOTAL = ACT1 + ACT2 + ACT3 + ACT4;

/** Fade from and to black at the very ends; every other cut is hard or motivated. */
const Bookends: React.FC = () => {
  const f = useCurrentFrame();
  const o = Math.max(
    interpolate(f, [0, 6], [1, 0], { extrapolateRight: 'clamp' }),
    interpolate(f, [TOTAL - 20, TOTAL], [0, 1], { extrapolateLeft: 'clamp' }),
  );
  return <AbsoluteFill style={{ background: '#000', opacity: o, pointerEvents: 'none' }} />;
};

// The soundtrack slots. Each plays only once its file exists in public/audio/.
const has = (n: string) => getStaticFiles().some((f) => f.name === n);
const A1 = ACT1;
const A3 = ACT1 + ACT2;
const A4 = ACT1 + ACT2 + ACT3;
const CUES: { file: string; at: number; volume?: number }[] = [
  { file: 'audio/vo/01-mother.mp3', at: 762 }, // "बेटा, सो जाओ…" over the closed book
  { file: 'audio/vo/02-never-the-exam.mp3', at: A4 + 30 },
  { file: 'audio/vo/03-spend-tonight.mp3', at: A4 + 140 },
  { file: 'audio/vo/04-we-prepare.mp3', at: A4 + 250 },
];

const Soundtrack: React.FC = () => (
  <>
    {has('audio/music.mp3') ? <Audio src={staticFile('audio/music.mp3')} volume={(f) => (f > A1 && f < A1 + 70 ? 0.15 : 0.8)} /> : null}
    {CUES.filter((c) => has(c.file)).map((c) => (
      <Sequence key={c.file} from={c.at}>
        <Audio src={staticFile(c.file)} volume={c.volume ?? 1} />
      </Sequence>
    ))}
  </>
);
void A3;

export const Film: React.FC = () => (
  <AbsoluteFill style={{ background: '#000' }}>
    <Soundtrack />
    <Sequence durationInFrames={ACT1}><Act1 /></Sequence>
    <Sequence from={ACT1} durationInFrames={ACT2}><Act2 /></Sequence>
    <Sequence from={ACT1 + ACT2} durationInFrames={ACT3}><Act3 /></Sequence>
    <Sequence from={ACT1 + ACT2 + ACT3} durationInFrames={ACT4}><Act4 /></Sequence>
    <Grain opacity={0.1} />
    <Bookends />
  </AbsoluteFill>
);
