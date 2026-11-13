// Renders review frames into out/stills, bundling once.
import { bundle } from '@remotion/bundler';
import { renderStill, selectComposition } from '@remotion/renderer';
import path from 'node:path';
import fs from 'node:fs';
const frames = process.argv.slice(2).map(Number);
const serveUrl = await bundle({ entryPoint: path.resolve('src/index.ts') });
const composition = await selectComposition({ serveUrl, id: process.env.COMP || 'LaunchFilm' });
fs.mkdirSync(`out/${process.env.COMP || 'stills'}`, { recursive: true });
for (const frame of frames) {
  await renderStill({ serveUrl, composition, frame, output: `out/${process.env.COMP || 'stills'}/f${String(frame).padStart(4, '0')}.jpg`, imageFormat: 'jpeg', jpegQuality: 80, scale: 0.5 });
  console.log('still', frame);
}
