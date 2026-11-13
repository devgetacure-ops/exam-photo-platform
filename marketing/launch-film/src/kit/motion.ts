import { Easing, interpolate, spring } from 'remotion';

// One easing vocabulary for the whole film, so every move feels like the same hand.
export const easeOut = Easing.bezier(0.16, 1, 0.3, 1); // settle
export const easeInOut = Easing.bezier(0.65, 0, 0.35, 1); // dolly
export const easeIn = Easing.bezier(0.7, 0, 0.84, 0); // leave

export const lerp = (
  f: number,
  [a, b]: [number, number],
  [from, to]: [number, number],
  ease = easeInOut,
) => interpolate(f, [a, b], [from, to], { easing: ease, extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });

export const fade = (f: number, inAt: number, inLen: number, outAt?: number, outLen = 8) => {
  const a = interpolate(f, [inAt, inAt + inLen], [0, 1], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  if (outAt === undefined) return a;
  const b = interpolate(f, [outAt, outAt + outLen], [1, 0], { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' });
  return Math.min(a, b);
};

// A stamp: arrives big, overshoots into the paper, settles. Physical, not bouncy.
export const stamp = (f: number, at: number, fps: number) =>
  spring({ frame: f - at, fps, config: { damping: 14, stiffness: 260, mass: 0.6 } });

export const settle = (f: number, at: number, fps: number, damping = 20) =>
  spring({ frame: f - at, fps, config: { damping, stiffness: 120, mass: 0.9 } });

// Deterministic pseudo-random, so renders are identical every time.
export const rand = (seed: number) => {
  const x = Math.sin(seed * 12.9898 + 78.233) * 43758.5453;
  return x - Math.floor(x);
};

// Handheld: layered slow noise, amplitude in px. Night one breathes; night two does not.
export const handheld = (f: number, amp: number, seed = 1) => {
  const n = (k: number, s: number) => Math.sin(f / k + s) * 0.6 + Math.sin(f / (k * 0.37) + s * 2.1) * 0.4;
  return { x: n(23, seed) * amp, y: n(29, seed + 4) * amp, r: n(41, seed + 9) * amp * 0.04 };
};
