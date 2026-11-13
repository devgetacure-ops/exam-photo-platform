import React from 'react';
import { Img, staticFile } from 'remotion';
import { C, F } from './theme';

// ---- physical props, drawn in the product's paper-and-ink language ----------

/** Wall clock. Time is given in minutes past midnight-ish (e.g. 23*60+14). */
export const Clock: React.FC<{ minutes: number; size?: number; face?: string; ink?: string }> = ({
  minutes,
  size = 520,
  face = C.paper,
  ink = C.ink,
}) => {
  const h = ((minutes / 60) % 12) * 30;
  const m = (minutes % 60) * 6;
  const ticks = Array.from({ length: 60 }, (_, i) => i);
  return (
    <svg width={size} height={size} viewBox="-110 -110 220 220">
      <circle r={104} fill={ink} />
      <circle r={96} fill={face} />
      {ticks.map((i) => {
        const long = i % 5 === 0;
        return (
          <line
            key={i}
            x1={0}
            y1={-90}
            x2={0}
            y2={long ? -76 : -84}
            stroke={ink}
            strokeWidth={long ? 4 : 1.4}
            transform={`rotate(${i * 6})`}
          />
        );
      })}
      {[12, 3, 6, 9].map((n, i) => (
        <text
          key={n}
          x={Math.sin((i * Math.PI) / 2) * 60}
          y={-Math.cos((i * Math.PI) / 2) * 60 + 2}
          textAnchor="middle"
          dominantBaseline="middle"
          fontFamily={F.display}
          fontWeight={900}
          fontSize={22}
          fill={ink}
        >
          {n}
        </text>
      ))}
      <line x1={0} y1={10} x2={0} y2={-48} stroke={ink} strokeWidth={7} strokeLinecap="square" transform={`rotate(${h})`} />
      <line x1={0} y1={14} x2={0} y2={-74} stroke={ink} strokeWidth={4} strokeLinecap="square" transform={`rotate(${m})`} />
      <line x1={0} y1={18} x2={0} y2={-80} stroke={C.signal} strokeWidth={1.6} transform={`rotate(${(minutes * 360) % 360})`} />
      <circle r={5} fill={C.signal} />
    </svg>
  );
};

/** A phone, matte and flat-edged like the brand: a hard ink body, no glossy render. */
export const Phone: React.FC<{
  width?: number;
  children?: React.ReactNode;
  src?: string;
  scrollY?: number;
  shadow?: boolean;
}> = ({ width = 520, children, src, scrollY = 0, shadow = true }) => {
  const height = width * (844 / 390);
  const bezel = width * 0.035;
  return (
    <div
      style={{
        width: width + bezel * 2,
        height: height + bezel * 2,
        background: C.ink,
        borderRadius: width * 0.13,
        padding: bezel,
        boxShadow: shadow ? '0 60px 90px rgba(0,0,0,0.35), 0 18px 30px rgba(0,0,0,0.25)' : undefined,
        position: 'relative',
      }}
    >
      <div
        style={{
          width,
          height,
          borderRadius: width * 0.105,
          overflow: 'hidden',
          position: 'relative',
          background: C.paper,
        }}
      >
        {src ? (
          <Img src={staticFile(src)} style={{ width, position: 'absolute', top: -scrollY, left: 0 }} />
        ) : null}
        {children}
        {/* the camera island */}
        <div
          style={{
            position: 'absolute',
            top: width * 0.025,
            left: '50%',
            width: width * 0.28,
            height: width * 0.07,
            transform: 'translateX(-50%)',
            background: C.ink,
            borderRadius: 999,
          }}
        />
      </div>
    </div>
  );
};

/** A laptop, for the one moment the desktop gets on screen. */
export const Laptop: React.FC<{ width?: number; src: string }> = ({ width = 900, src }) => {
  const screenH = width * (900 / 1440);
  return (
    <div style={{ width: width + 40, position: 'relative' }}>
      <div style={{ background: C.ink, padding: 20, paddingBottom: 26, borderRadius: '18px 18px 0 0' }}>
        <Img src={staticFile(src)} style={{ width, height: screenH, display: 'block', objectFit: 'cover', objectPosition: 'top' }} />
      </div>
      <div
        style={{
          height: 22,
          marginLeft: -60,
          marginRight: -60,
          background: '#2a2926',
          borderRadius: '0 0 26px 26px',
          borderTop: `3px solid ${C.ink}`,
        }}
      />
    </div>
  );
};

/** Ink stamp, the brand's offset-shadow box turned into a rubber stamp impression. */
export const Stamp: React.FC<{ text: string; color?: string; size?: number; rotate?: number; fill?: string }> = ({
  text,
  color = C.signal,
  size = 54,
  rotate = -4,
  fill = 'transparent',
}) => (
  <div
    style={{
      display: 'inline-block',
      padding: `${size * 0.18}px ${size * 0.4}px ${size * 0.08}px`,
      border: `${Math.max(4, size * 0.09)}px solid ${color}`,
      color,
      background: fill,
      fontFamily: F.display,
      fontWeight: 900,
      fontSize: size,
      lineHeight: 1,
      letterSpacing: '0.02em',
      textTransform: 'uppercase',
      transform: `rotate(${rotate}deg)`,
      whiteSpace: 'nowrap',
      // a rubber stamp never inks evenly
      maskImage:
        'radial-gradient(circle at 30% 40%, #000 60%, rgba(0,0,0,0.75) 100%), linear-gradient(#000,#000)',
    }}
  >
    {text}
  </div>
);

/** The thirteen-cell wordmark, drawn cell by cell. */
export const Wordmark: React.FC<{ cell?: number; reveal?: number; color?: string; bg?: string }> = ({
  cell = 64,
  reveal = 13,
  color = C.ink,
  bg = C.paper,
}) => {
  const letters = 'EXAMUPLOADKIT'.split('');
  return (
    <div style={{ display: 'flex', border: `${cell * 0.08}px solid ${color}`, background: bg }}>
      {letters.map((l, i) => {
        const v = Math.max(0, Math.min(1, reveal - i));
        return (
          <div
            key={i}
            style={{
              width: cell * 0.62,
              height: cell,
              borderLeft: i === 0 ? 'none' : `${cell * 0.04}px solid ${color}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontFamily: F.display,
              fontWeight: 800,
              fontSize: cell * 0.62,
              color,
              opacity: v,
              transform: `translateY(${(1 - v) * cell * 0.3}px)`,
            }}
          >
            {l}
          </div>
        );
      })}
    </div>
  );
};
