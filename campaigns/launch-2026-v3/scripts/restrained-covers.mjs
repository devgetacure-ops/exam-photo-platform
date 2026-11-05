import fs from 'node:fs/promises';
import path from 'node:path';
import sharp from '../../../apps/web/node_modules/sharp/dist/index.cjs';

const out=path.resolve('campaigns/launch-2026-v3/cover-mockups');
const ids=['exam','upload','kit'];
const rows=[{left:1028,top:96,width:744,height:224},{left:844,top:316,width:1112,height:224},{left:1120,top:536,width:560,height:224}];
const orange='#f04e23';
const variants=['01-wordmark','02-inset','03-band'];
await fs.mkdir(out,{recursive:true});
const grids=[];
for(const variant of variants){
 for(const theme of ['light','dark']){
  const dir=path.join(out,`${variant}-${theme}`); await fs.mkdir(dir,{recursive:true});
  const asset=`apps/web/public/brand/examuploadkit-stacked-${theme}.png`;
  const pixel=await sharp(asset).extract({left:0,top:0,width:1,height:1}).removeAlpha().raw().toBuffer();
  const bg=`rgb(${pixel[0]},${pixel[1]},${pixel[2]})`;
  const fg=theme==='dark'?'#efede6':'#151412';
  const line=theme==='dark'?'#35332f':'#dad7cf';
  const previews=[];
  for(let i=0;i<3;i++){
   // The same resize factor preserves letter scale across the three original rows.
   const h=variant==='02-inset'?164:180;
   const logo=await sharp(asset).extract(rows[i]).resize({height:h}).png().toBuffer();
   const m=await sharp(logo).metadata();
   const x=Math.round((1080-m.width)/2),y=Math.round((1350-h)/2);
   let decoration='';
   if(variant==='01-wordmark') decoration=`<rect x='${i===0?96:i===1?510:924}' y='1025' width='60' height='8' fill='${orange}'/>`;
   if(variant==='02-inset') decoration=`<rect x='48' y='48' width='984' height='1254' fill='none' stroke='${line}' stroke-width='2'/><rect x='48' y='48' width='${[328,656,984][i]}' height='7' fill='${orange}'/><text x='96' y='170' fill='${fg}' font-family='Bahnschrift' font-size='21' letter-spacing='3'>${['01','02','03'][i]}</text><text x='96' y='1190' fill='${fg}' font-family='Bahnschrift' font-size='23'>${['Your examination.','Your files.','Your upload kit.'][i]}</text>`;
   if(variant==='03-band') decoration=`<rect x='0' y='410' width='1080' height='530' fill='none' stroke='${line}' stroke-width='2'/><rect x='0' y='940' width='1080' height='14' fill='${orange}'/><text x='96' y='1130' fill='${fg}' font-family='Bahnschrift' font-size='28'>${['You prepare','for the exam.','We prepare the files.'][i]}</text>`;
   const svg=Buffer.from(`<svg xmlns='http://www.w3.org/2000/svg' width='1080' height='1350'><rect width='1080' height='1350' fill='${bg}'/>${decoration}</svg>`);
   const result=await sharp(svg).composite([{input:logo,left:x,top:y}]).png().toBuffer();
   await fs.writeFile(path.join(dir,`${ids[i]}.png`),result);
   previews.push({input:await sharp(result).resize(360,450).png().toBuffer(),left:i*368,top:0});
  }
  const grid=await sharp({create:{width:1096,height:450,channels:3,background:theme==='dark'?'#292929':'#e7e5e1'}}).composite(previews).png().toBuffer();
  await fs.writeFile(path.join(dir,'grid.png'),grid); grids.push({variant,theme,grid});
 }
}
const layers=[];
for(let i=0;i<grids.length;i++){
 const {variant,theme,grid}=grids[i];
 const x=(i%2)*1132+24,y=Math.floor(i/2)*530+60;
 const label=Buffer.from(`<svg xmlns='http://www.w3.org/2000/svg' width='1096' height='36'><text x='0' y='25' fill='#262626' font-family='Bahnschrift' font-size='22'>${String.fromCharCode(65+Math.floor(i/2))} / ${variant.slice(3).toUpperCase()} — ${theme.toUpperCase()}</text></svg>`);
 layers.push({input:label,left:x,top:y-40},{input:grid,left:x,top:y});
}
await sharp({create:{width:2264,height:1600,channels:3,background:'#eeece7'}}).composite(layers).png().toFile(path.join(out,'comparison.png'));
await fs.writeFile(path.join(out,'README.md'),'# Cover mockups\n\nThree compositions, each in light and dark: A Wordmark, B Inset, C Band. Each folder contains three 1080 × 1350 covers and a grid preview. Original logo excerpts share identical scale and baseline within every set. Existing campaign covers have not been replaced.\n');
console.log('Created six complete grid mockups and eighteen cover files.');
