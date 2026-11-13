import React from 'react';
import { Composition, registerRoot } from 'remotion';
import { Film, TOTAL } from './Film';
import { TheFrame, FRAME_TOTAL, Reframed } from './frame/TheFrame';
import { FPS, H, W } from './kit/theme';

const Root: React.FC = () =>
  React.createElement(
    React.Fragment,
    null,
    // v2 — the launch film: 4:5 master for the LinkedIn feed
    React.createElement(Composition, { id: 'TheFrame', component: TheFrame, durationInFrames: FRAME_TOTAL, fps: FPS, width: W, height: H }),
    // 9:16 for LinkedIn's vertical feed, Reels and Shorts
    React.createElement(Composition, {
      id: 'TheFrame-9x16',
      component: Reframed,
      durationInFrames: FRAME_TOTAL,
      fps: FPS,
      width: 1080,
      height: 1920,
    }),
    // 16:9 for the website and YouTube
    React.createElement(Composition, {
      id: 'TheFrame-16x9',
      component: Reframed,
      durationInFrames: FRAME_TOTAL,
      fps: FPS,
      width: 1920,
      height: 1080,
    }),
    // v1 — the first animatic, kept for reference
    React.createElement(Composition, { id: 'LaunchFilm', component: Film, durationInFrames: TOTAL, fps: FPS, width: W, height: H }),
  );

registerRoot(Root);
