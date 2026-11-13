import React from 'react';
import { C } from '../kit/theme';

/**
 * A phone with real thickness, in CSS 3D: a front with its glass, and four edges.
 * Rotate the parent; the edges turn with it, so the phone reads as an object, not a sticker.
 */
export const Phone3D: React.FC<{
  w: number; // screen width
  rx?: number;
  ry?: number;
  rz?: number;
  glare?: number; // 0..1 position of the light sweep across the glass
  bezel?: number; // 0..1 how much of the body has formed around the screen
  children?: React.ReactNode;
}> = ({ w, rx = 0, ry = 0, rz = 0, glare = 0.3, bezel = 1, children }) => {
  const h = w * (844 / 390);
  const b = w * 0.04 * bezel;
  const depth = w * 0.06 * bezel;
  const radius = w * 0.12 * bezel;
  const bodyW = w + b * 2;
  const bodyH = h + b * 2;
  const edge: React.CSSProperties = { position: 'absolute', background: 'linear-gradient(90deg,#1b1b1a,#3a3936 45%,#141413)' };
  return (
    <div style={{ width: bodyW, height: bodyH, transformStyle: 'preserve-3d', transform: `rotateX(${rx}deg) rotateY(${ry}deg) rotateZ(${rz}deg)` }}>
      {/* edges */}
      <div style={{ ...edge, left: bodyW - depth / 2, top: radius, width: depth, height: bodyH - radius * 2, transform: 'rotateY(90deg)' }} />
      <div style={{ ...edge, left: -depth / 2, top: radius, width: depth, height: bodyH - radius * 2, transform: 'rotateY(-90deg)' }} />
      <div style={{ ...edge, left: radius, top: -depth / 2, width: bodyW - radius * 2, height: depth, transform: 'rotateX(90deg)' }} />
      <div style={{ ...edge, left: radius, top: bodyH - depth / 2, width: bodyW - radius * 2, height: depth, transform: 'rotateX(-90deg)' }} />
      {/* back plate, so the far edge never shows through */}
      <div style={{ position: 'absolute', inset: 0, borderRadius: radius, background: '#111', transform: `translateZ(${-depth / 2}px)` }} />
      {/* front */}
      <div
        style={{
          position: 'absolute', inset: 0, borderRadius: radius, background: C.ink, padding: b, transform: `translateZ(${depth / 2}px)`,
          boxShadow: `inset 0 0 0 ${Math.max(1, w * 0.004)}px #4a4844`,
        }}
      >
        <div style={{ width: w, height: h, borderRadius: Math.max(0, radius - b), overflow: 'hidden', position: 'relative', background: C.paper }}>
          {children}
          {/* the island */}
          <div style={{ position: 'absolute', top: w * 0.025, left: '50%', width: w * 0.27, height: w * 0.07, transform: 'translateX(-50%)', background: '#000', borderRadius: 99, opacity: bezel }} />
          {/* glass: a soft sweep of the key light */}
          <div
            style={{
              position: 'absolute', inset: 0, pointerEvents: 'none', mixBlendMode: 'screen',
              background: `linear-gradient(115deg, rgba(255,255,255,0) ${glare * 100 - 22}%, rgba(255,245,235,0.16) ${glare * 100 - 6}%, rgba(255,255,255,0.03) ${glare * 100 + 4}%, rgba(255,255,255,0) ${glare * 100 + 22}%)`,
            }}
          />
        </div>
      </div>
    </div>
  );
};
