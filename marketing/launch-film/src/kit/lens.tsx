import React from 'react';
import { AbsoluteFill, useCurrentFrame } from 'remotion';
import { C, F } from './theme';

// ---- the lens: what makes it read as photographed, not generated ----------

/** 35mm-ish grain that changes every frame. */
export const Grain: React.FC<{ opacity?: number }> = ({ opacity = 0.12 }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ pointerEvents: 'none', mixBlendMode: 'overlay', opacity }}>
      <svg width="100%" height="100%">
        <filter id={`g${f}`}>
          <feTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves={2} seed={f % 97} stitchTiles="stitch" />
          <feColorMatrix type="saturate" values="0" />
        </filter>
        <rect width="100%" height="100%" filter={`url(#g${f})`} />
      </svg>
    </AbsoluteFill>
  );
};

/** Optical falloff at the corners. */
export const Vignette: React.FC<{ strength?: number }> = ({ strength = 0.55 }) => (
  <AbsoluteFill
    style={{
      pointerEvents: 'none',
      background: `radial-gradient(ellipse 75% 70% at 50% 48%, rgba(0,0,0,0) 55%, rgba(0,0,0,${strength}) 100%)`,
    }}
  />
);

/** Colour grade as a tint layer: cold for night one, warm for night two. */
export const Grade: React.FC<{ tone: 'cold' | 'warm' | 'dawn'; amount?: number }> = ({ tone, amount = 1 }) => {
  const tint = tone === 'cold' ? '#1f5266' : tone === 'warm' ? '#ff9a3d' : '#ffd9a8';
  return <AbsoluteFill style={{ pointerEvents: 'none', background: tint, mixBlendMode: 'soft-light', opacity: 0.55 * amount }} />;
};

/** Paper fibre, multiplied over anything that is meant to be paper. */
export const PaperTexture: React.FC<{ opacity?: number; seed?: number }> = ({ opacity = 0.35, seed = 3 }) => (
  <AbsoluteFill style={{ pointerEvents: 'none', mixBlendMode: 'multiply', opacity }}>
    <svg width="100%" height="100%">
      <filter id={`p${seed}`}>
        <feTurbulence type="fractalNoise" baseFrequency="0.012 0.5" numOctaves={3} seed={seed} />
        <feColorMatrix type="matrix" values="0 0 0 0 0.93  0 0 0 0 0.91  0 0 0 0 0.86  0 0 0 -0.9 1.05" />
      </filter>
      <rect width="100%" height="100%" filter={`url(#p${seed})`} />
    </svg>
  </AbsoluteFill>
);

/** A virtual camera body: dolly (scale), track (x/y), dutch (rotate), focus (blur). */
export const Camera: React.FC<{
  scale?: number;
  x?: number;
  y?: number;
  rotate?: number;
  blur?: number;
  origin?: string;
  children: React.ReactNode;
}> = ({ scale = 1, x = 0, y = 0, rotate = 0, blur = 0, origin = '50% 50%', children }) => (
  <AbsoluteFill
    style={{
      transform: `translate(${x}px, ${y}px) scale(${scale}) rotate(${rotate}deg)`,
      transformOrigin: origin,
      filter: blur > 0.05 ? `blur(${blur}px)` : undefined,
    }}
  >
    {children}
  </AbsoluteFill>
);

/** Burned-in caption. LinkedIn plays muted; the words carry the film. */
export const Caption: React.FC<{ text: string; opacity?: number; y?: number; tone?: 'light' | 'dark'; size?: number }> = ({
  text,
  opacity = 1,
  y = 1130,
  tone = 'light',
  size = 46,
}) => (
  <div
    style={{
      position: 'absolute',
      left: 80,
      right: 80,
      top: y,
      textAlign: 'center',
      fontFamily: F.body,
      fontWeight: 600,
      fontSize: size,
      lineHeight: 1.2,
      color: tone === 'light' ? C.paper : C.ink,
      textShadow: tone === 'light' ? '0 2px 18px rgba(0,0,0,0.85)' : 'none',
      opacity,
      letterSpacing: '-0.005em',
    }}
  >
    {text}
  </div>
);

/** Letterbox-free safe frame guide is not drawn; kept as constants for 9:16 reframes. */
export const SAFE = { top: 90, bottom: 1260, left: 64, right: 1016 };
