import { loadFont as loadShoulders } from '@remotion/google-fonts/BigShoulders';
import { loadFont as loadAnek } from '@remotion/google-fonts/AnekLatin';
import { loadFont as loadAnekHi } from '@remotion/google-fonts/AnekDevanagari';
import { loadFont as loadAnekBn } from '@remotion/google-fonts/AnekBangla';
import { loadFont as loadAnekTa } from '@remotion/google-fonts/AnekTamil';
import { loadFont as loadAnekTe } from '@remotion/google-fonts/AnekTelugu';
import { loadFont as loadAnekGu } from '@remotion/google-fonts/AnekGujarati';
import { loadFont as loadAnekPa } from '@remotion/google-fonts/AnekGurmukhi';
import { loadFont as loadAnekOr } from '@remotion/google-fonts/AnekOdia';
import { loadFont as loadAnekKn } from '@remotion/google-fonts/AnekKannada';
import { loadFont as loadAnekMl } from '@remotion/google-fonts/AnekMalayalam';
import { loadFont as loadType } from '@remotion/google-fonts/SpecialElite';

// The product's own identity, taken from apps/web/src/app/system.css.
export const C = {
  paper: '#faf9f6',
  paper2: '#f2f0ea',
  ink: '#111110',
  ink70: '#3a3833',
  ink55: '#55524b',
  ink40: '#6b675d',
  hairline: '#dedacf',
  signal: '#f04e23',
  signalDeep: '#c1370e',
  signalSoft: '#fde7e0',
  okLine: '#165c33',
  okFill: '#d9efe0',
  night: '#0b0f14',
  error: '#d12b2b',
};

export const F = {
  display: loadShoulders('normal', { weights: ['800', '900'] }).fontFamily,
  body: loadAnek('normal', { weights: ['400', '500', '600', '700'] }).fontFamily,
  hindi: loadAnekHi('normal', { weights: ['500', '700'] }).fontFamily,
  bangla: loadAnekBn('normal', { weights: ['600'] }).fontFamily,
  tamil: loadAnekTa('normal', { weights: ['600'] }).fontFamily,
  telugu: loadAnekTe('normal', { weights: ['600'] }).fontFamily,
  gujarati: loadAnekGu('normal', { weights: ['600'] }).fontFamily,
  gurmukhi: loadAnekPa('normal', { weights: ['600'] }).fontFamily,
  odia: loadAnekOr('normal', { weights: ['600'] }).fontFamily,
  kannada: loadAnekKn('normal', { weights: ['600'] }).fontFamily,
  malayalam: loadAnekMl('normal', { weights: ['600'] }).fontFamily,
  type: loadType('normal', { weights: ['400'] }).fontFamily,
};

export const W = 1080;
export const H = 1350;
export const FPS = 30;
