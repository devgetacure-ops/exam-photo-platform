import React from 'react';
import { Img, getStaticFiles, staticFile } from 'remotion';

/**
 * The candidate's photograph.
 *
 * public/photo/source.jpg  — the phone selfie she starts with (cluttered room, yellow bulb)
 * public/photo/prepared.jpg — what the real engine made of it
 *
 * Both are generated, fictional people; never a real candidate. Until they exist the film
 * draws an ink stand-in so every scene still plays.
 */
const has = (name: string) => getStaticFiles().some((f) => f.name === name);

export const hasSource = () => has('photo/source.jpg');
export const hasPrepared = () => has('photo/prepared.jpg');

type Variant = 'source' | 'prepared';

export const Portrait: React.FC<{
  variant: Variant;
  width: number;
  height: number;
  /** 0 = room behind her, 1 = clean white */
  whiten?: number;
  style?: React.CSSProperties;
  objectPosition?: string;
}> = ({ variant, width, height, whiten, style, objectPosition = '50% 35%' }) => {
  const file = variant === 'source' ? 'photo/source.jpg' : 'photo/prepared.jpg';
  const w = whiten ?? (variant === 'prepared' ? 1 : 0);
  if (has(file)) {
    return (
      <div style={{ width, height, overflow: 'hidden', position: 'relative', ...style }}>
        <Img src={staticFile(file)} style={{ width: '100%', height: '100%', objectFit: 'cover', objectPosition }} />
      </div>
    );
  }
  return <InkStandIn width={width} height={height} whiten={w} style={style} />;
};

/** A drawn stand-in: head-and-shoulders, a cluttered bedroom wall that can wash to white. */
const InkStandIn: React.FC<{ width: number; height: number; whiten: number; style?: React.CSSProperties }> = ({
  width,
  height,
  whiten,
  style,
}) => (
  <div style={{ width, height, overflow: 'hidden', position: 'relative', ...style }}>
    <svg width={width} height={height} viewBox="0 0 300 400" preserveAspectRatio="xMidYMid slice">
      {/* the room: yellow bulb light, almirah, calendar, shelf */}
      <rect width="300" height="400" fill="#c9a861" />
      <rect x="0" y="0" width="300" height="400" fill="url(#bulb)" />
      <rect x="196" y="40" width="110" height="300" fill="#6d6a63" />
      <rect x="200" y="46" width="50" height="290" fill="#7c7970" />
      <rect x="18" y="60" width="62" height="78" fill="#efe6cf" />
      <rect x="18" y="60" width="62" height="16" fill="#b8402a" />
      <rect x="0" y="210" width="90" height="8" fill="#5a4a33" />
      <rect x="8" y="182" width="12" height="28" fill="#2f5d7a" />
      <rect x="22" y="188" width="10" height="22" fill="#8a3b2c" />
      <rect x="34" y="178" width="14" height="32" fill="#3d6b44" />
      <rect width="300" height="400" fill="#ffffff" opacity={whiten} />
      {/* her */}
      <path d="M40 400 C 50 320, 95 300, 150 296 C 205 300, 250 320, 260 400 Z" fill="#2b4a6b" />
      <path d="M128 270 L 172 270 L 168 305 L 132 305 Z" fill="#a9785a" />
      <ellipse cx="150" cy="205" rx="56" ry="70" fill="#b5835f" />
      <path d="M92 200 C 88 130, 125 118, 152 120 C 190 120, 214 140, 208 205 C 204 170, 188 150, 150 150 C 118 152, 98 170, 92 200 Z" fill="#17120e" />
      <ellipse cx="128" cy="212" rx="7" ry="4" fill="#1b130d" />
      <ellipse cx="172" cy="212" rx="7" ry="4" fill="#1b130d" />
      <path d="M140 248 Q 150 254 160 248" stroke="#6e3f2e" strokeWidth="3" fill="none" />
      <defs>
        <radialGradient id="bulb" cx="0.2" cy="0.05" r="0.9">
          <stop offset="0" stopColor="#fff2b0" stopOpacity="0.7" />
          <stop offset="1" stopColor="#4a3a20" stopOpacity="0.5" />
        </radialGradient>
      </defs>
    </svg>
  </div>
);
