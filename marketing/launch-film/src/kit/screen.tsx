import React from 'react';
import { Img, staticFile } from 'remotion';

// Real captures of examuploadkit.com at 390 pt wide, @3x. Fixed bars captured on their own
// so the page can scroll beneath them exactly as it does on a phone.
export const PAGES = {
  jee: { page: 'ui/m-jee-clean.png', top: 'ui/m-jee-topbar.png', bottom: 'ui/m-jee-bottombar.png', h: 9159, topH: 270, botH: 228 },
  jeeHi: { page: 'ui/m-jee-hi-clean.png', top: 'ui/m-jee-hi-topbar.png', bottom: 'ui/m-jee-hi-bottombar.png', h: 8958, topH: 270, botH: 228 },
  home: { page: 'ui/m-home-clean.png', top: 'ui/m-home-topbar.png', bottom: 'ui/m-home-bottombar.png', h: 10800, topH: 168, botH: 228 },
} as const;

export type PageKey = keyof typeof PAGES;

/** A live page inside a phone screen. scroll is in CSS points of the real page (390 pt wide). */
export const LivePage: React.FC<{ page: PageKey; width: number; scroll: number; bars?: boolean }> = ({
  page,
  width,
  scroll,
  bars = true,
}) => {
  const p = PAGES[page];
  const s = width / 1170; // capture px -> screen px
  const topH = bars ? p.topH * s : 0;
  return (
    <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', background: '#faf9f6' }}>
      <Img src={staticFile(p.page)} style={{ position: 'absolute', left: 0, top: topH - scroll * 3 * s, width }} />
      {bars ? (
        <>
          <Img src={staticFile(p.top)} style={{ position: 'absolute', left: 0, top: 0, width }} />
          <Img src={staticFile(p.bottom)} style={{ position: 'absolute', left: 0, bottom: 0, width }} />
        </>
      ) : null}
    </div>
  );
};
