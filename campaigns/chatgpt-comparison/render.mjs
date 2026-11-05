import fs from 'node:fs/promises';
import path from 'node:path';
import sharp from '../../apps/web/node_modules/sharp/dist/index.cjs';

const out=path.resolve('campaigns/chatgpt-comparison');
await fs.mkdir(out,{recursive:true});
const esc=s=>s.replaceAll('&','&amp;').replaceAll('<','&lt;');
const text=(lines,x,y,size=36,color='#f6f4ef',weight=400,gap=size*1.25)=>`<text x="${x}" y="${y}" fill="${color}" font-family="Bahnschrift" font-size="${size}" font-weight="${weight}">${lines.map((s,i)=>`<tspan x="${x}" dy="${i?gap:0}">${esc(s)}</tspan>`).join('')}</text>`;
const panel=(x,y,w,h)=>`<rect x="${x}" y="${y}" width="${w}" height="${h}" rx="28" fill="url(#glass)" stroke="#ffffff" stroke-opacity=".16"/>`;
const line=(y)=>`<path d="M76 ${y}H1004" stroke="#ffffff" stroke-opacity=".15"/>`;
const dot=(x,y)=>`<circle cx="${x}" cy="${y}" r="5" fill="#f97758"/>`;
const brand=await fs.readFile('apps/web/public/brand/examuploadkit-stacked-dark.png');
const logo=`<image href="data:image/png;base64,${brand.toString('base64')}" x="812" y="49" width="192" height="64" preserveAspectRatio="xMidYMid meet"/>`;
function svg(content,i){return `<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350"><defs><radialGradient id="glow"><stop stop-color="#a82252" stop-opacity=".45"/><stop offset="1" stop-color="#090b10" stop-opacity="0"/></radialGradient><radialGradient id="blue"><stop stop-color="#28759a" stop-opacity=".35"/><stop offset="1" stop-color="#090b10" stop-opacity="0"/></radialGradient><linearGradient id="glass" x2=".8" y2="1"><stop stop-color="#ffffff" stop-opacity=".105"/><stop offset="1" stop-color="#ffffff" stop-opacity=".02"/></linearGradient></defs><rect width="1080" height="1350" fill="#090b10"/><ellipse cx="${i%2?150:960}" cy="330" rx="620" ry="610" fill="url(#glow)"/><ellipse cx="900" cy="1230" rx="550" ry="480" fill="url(#blue)"/>${logo}${content}${line(1232)}${text(['EXAMUPLOADKIT.COM'],76,1284,19,'#b7bdc8',500)}${text([`${i} / 4${i<4?'    SWIPE →':''}`],846,1284,19,'#b7bdc8')}</svg>`;}
const slides=[
  text(['“Can’t ChatGPT','do this?”'],76,252,84,'#f6f4ef',600,98)+text(['Let’s talk about the whole upload.'],80,436,33,'#b9bfca')+
  panel(76,532,928,408)+text(['A clean background'],118,611,45,'#f6f4ef',500)+text(['is one part of the job.'],118,668,45,'#f6f4ef',500)+line(712)+text(['DIMENSIONS     FILE SIZE     FORMAT'],118,772,28,'#efab9c',500)+text(['FRAMING     READABILITY     FILE NAME'],118,831,28,'#efab9c',500)+
  text(['Your exam sets the requirements.'],76,1046,41,'#f6f4ef',500)+text(['The final file has to meet them together.'],76,1103,32,'#b9bfca'),
  text(['Right-looking isn’t','the whole requirement.'],76,230,66,'#f6f4ef',600,80)+text(['What needs attention before you submit'],76,412,31,'#b9bfca')+
  [['01','Dimensions + framing','The required shape, without stretching.'],['02','File size + format','The allowed KB range and file type.'],['03','Identity + readability','Your face stays yours. Your writing stays clear.'],['04','Exam-specific details','Naming, DPI or coverage when specified.']].map((r,i)=>{let y=480+i*159;return text([r[0]],78,y+42,24,'#f97758')+text([r[1]],150,y+43,39,'#f6f4ef',500)+text([r[2]],150,y+94,28,'#b9bfca')+line(y+127)}).join('')+text(['Requirements vary by exam and upload type.'],76,1178,25,'#b9bfca'),
  text(['Choose the exam.','Skip assembling','the instructions.'],76,238,72,'#f6f4ef',600,86)+
  `<path d="M122 607V964" stroke="#f97758" stroke-opacity=".4" stroke-width="2"/>`+
  [['Select your exam','Start with its stored upload requirements.'],['Upload the files','Prepare supported files in one workflow.'],['Review the preview','See the prepared result before you pay.']].map((r,i)=>{let y=590+i*158;return `<circle cx="122" cy="${y+20}" r="25" fill="#171b24" stroke="#ef8c72"/>`+text([String(i+1)],115,y+28,23,'#efab9c')+text([r[0]],182,y+27,39,'#f6f4ef',500)+text([r[1]],182,y+77,28,'#b9bfca')}).join('')+
  panel(76,1080,928,104)+text(['Less setup. Fewer tools to coordinate.'],112,1145,34,'#f6f4ef',500),
  text(['Yes, AI can help.','Here’s why we exist.'],76,240,69,'#f6f4ef',600,84)+
  panel(76,435,928,250)+text(['ChatGPT can process files too.'],112,499,35,'#f6f4ef',500)+text(['Free access includes tools, with usage limits.','Paid plans offer more access—not an','exam-specific acceptance guarantee.'],112,558,29,'#b9bfca',400,43)+
  text(['You bring the files.','ExamUploadKit brings','the exam-specific workflow.'],76,791,51,'#f6f4ef',500,65)+
  text(['Explore your exam →'],76,1056,43,'#efab9c',500)+text(['examuploadkit.com'],76,1114,33,'#f6f4ef')+text(['Review the result and the current official instructions.','Final acceptance rests with the examination authority.'],76,1170,22,'#b9bfca',400,30)
];
slides.splice(1,0,
  text(['All those tools.','Still one missed rule.'],76,229,72,'#f6f4ef',600,86)+
  text(['The DIY route can look like this:'],76,403,30,'#b9bfca')+
  [['AI image editor','Remove the background. Some also generate','formal clothing or recreate the photograph.'],['Resize website','Enter dimensions in pixels and resolution / DPI.'],['Compression website','Adjust the file size to the required KB range.'],['Rename the file','Match the requested name, where specified.']].map((r,i)=>{const y=460+i*139;return panel(76,y,928,118)+text([String(i+1).padStart(2,'0')],103,y+43,24,'#efab9c')+text([r[0]],169,y+40,31,'#f6f4ef',500)+text(r.slice(1),169,y+76,24,'#b9bfca',400,30)}).join('')+
  text(['Right pixels. Right KB. Wrong framing?'],76,1071,36,'#efab9c',500)+text(['It can still fail an exam’s framing or face-coverage rule.'],76,1117,27,'#f6f4ef')+text(['AI-generated clothing or facial edits can compromise authenticity.','Keep your identity intact; coverage requirements vary by exam.'],76,1167,22,'#b9bfca',400,30)
);
for(let i=0;i<slides.length;i++){
  const source=svg(slides[i],i+1).replace(`${i+1} / 4${i+1<4?'    SWIPE →':''}`,`${i+1} / 5${i+1<5?'    SWIPE →':''}`);
  await fs.writeFile(path.join(out,`0${i+1}.svg`),source);
  await sharp(Buffer.from(source)).png().toFile(path.join(out,`0${i+1}.png`));
}
const thumbs=await Promise.all(slides.map((_,i)=>sharp(path.join(out,`0${i+1}.png`)).resize(432,540).toBuffer()));
await sharp({create:{width:1296,height:1080,channels:3,background:'#090b10'}}).composite(thumbs.map((input,i)=>({input,left:(i%3)*432,top:Math.floor(i/3)*540}))).png().toFile(path.join(out,'preview.png'));
console.log('Rendered five 1080x1350 slides and preview.');
