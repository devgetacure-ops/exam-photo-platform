import sys, glob
from PIL import Image, ImageDraw
files = sorted(glob.glob('out/stills/*.jpg'))
start = int(sys.argv[1]); end = int(sys.argv[2]); out = sys.argv[3]
files = [f for f in files if start <= int(f[-8:-4]) <= end]
w, h = 270, 338; cols = 5
rows = (len(files) + cols - 1) // cols
sheet = Image.new('RGB', (cols * w, rows * (h + 20)), 'white')
d = ImageDraw.Draw(sheet)
for i, f in enumerate(files):
    im = Image.open(f).resize((w, h))
    x, y = (i % cols) * w, (i // cols) * (h + 20)
    sheet.paste(im, (x, y + 20)); d.text((x + 4, y + 4), f[-9:-4], fill='black')
sheet.save(out, quality=85)
