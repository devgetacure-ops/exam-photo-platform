import sys, glob
from PIL import Image, ImageDraw
d, a, b, out = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
fs = [f for f in sorted(glob.glob(d + '/*.jpg')) if a <= int(f[-8:-4]) <= b]
w, h, cols = 270, 338, 6
rows = (len(fs) + cols - 1) // cols
s = Image.new('RGB', (cols * w, rows * (h + 20)), 'white'); dr = ImageDraw.Draw(s)
for i, f in enumerate(fs):
    x, y = (i % cols) * w, (i // cols) * (h + 20)
    s.paste(Image.open(f).resize((w, h)), (x, y + 20)); dr.text((x + 4, y + 4), f[-8:-4], fill='black')
s.save(out, quality=85)
