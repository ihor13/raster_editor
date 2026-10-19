#!/usr/bin/env python3
"""Assemble tools/_frames/*.png into docs/demo.gif, plus a before/after still.

    python tools/build-gif.py

Width and frame delay are tuned for a README: wide enough to read the panels,
small enough that GitHub still loads it.
"""
import glob, os
from PIL import Image

FRAMES = sorted(glob.glob("tools/_frames/*.png"))
try:
    import json
    MARKS = json.load(open("tools/_frames/marks.json"))
except Exception:
    MARKS = {}
WIDTH = 900
DELAY = 150          # ms per frame
HOLD_LAST = 1600     # ms on the final frame
CANVAS = (76, 97, 993, 711)   # the canvas rectangle inside a 1320x800 capture

if not FRAMES:
    raise SystemExit("no frames — run tools/record-demo.mjs first")

os.makedirs("docs", exist_ok=True)

def scaled(path):
    im = Image.open(path).convert("RGB")
    return im.resize((WIDTH, round(im.height * WIDTH / im.width)), Image.LANCZOS)

# One palette shared by every frame, and disposal=1 so the encoder stores only
# what changed between frames. Together those take this GIF from ~5 MB to ~0.3 MB.
# The palette is built from a montage spanning the whole recording — taken from
# frame 0 alone it would miss every colour the photo introduces later.
# Median cut allocates palette entries by pixel count, and the chrome covers more
# of the screen than the artwork does — sampled from whole frames it spends the
# palette on panel greys and leaves the photo's colours to the nearest neighbour.
# So the montage is mostly canvas crops, with one whole frame for the chrome.
picks = [FRAMES[i] for i in (6, len(FRAMES)//3, 2*len(FRAMES)//3, len(FRAMES)-1)]
tiles = [Image.open(f).convert("RGB").crop(CANVAS) for f in picks]
cw, ch = tiles[0].size
chrome = scaled(FRAMES[len(FRAMES)//2])
montage = Image.new("RGB", (max(cw, chrome.width), ch * len(tiles) + chrome.height))
for i, t in enumerate(tiles):
    montage.paste(t, (0, i * ch))
montage.paste(chrome, (0, ch * len(tiles)))
palette = montage.quantize(colors=256, method=Image.MEDIANCUT)
imgs = [scaled(f).quantize(palette=palette, dither=Image.NONE) for f in FRAMES]

durations = [DELAY] * len(imgs)
durations[-1] = HOLD_LAST
durations[0] = 900

imgs[0].save("docs/demo.gif", save_all=True, append_images=imgs[1:],
             duration=durations, loop=0, optimize=True, disposal=1)
print("docs/demo.gif", round(os.path.getsize("docs/demo.gif") / 1024), "KB,", len(imgs), "frames")

# --- before / after still, cropped to the canvas area of the first and last frame
first = Image.open(FRAMES[MARKS.get("beforeFrame", 6)]).convert("RGB")
last = Image.open(FRAMES[MARKS.get("afterFrame", len(FRAMES) - 1)]).convert("RGB")
a, b = first.crop(CANVAS), last.crop(CANVAS)
w, h = a.size
gap = 14
sheet = Image.new("RGB", (w * 2 + gap, h), (18, 19, 22))
sheet.paste(a, (0, 0)); sheet.paste(b, (w + gap, 0))
sheet = sheet.resize((1000, round(sheet.height * 1000 / sheet.width)), Image.LANCZOS)
sheet.save("docs/before-after.png", optimize=True)
print("docs/before-after.png", round(os.path.getsize("docs/before-after.png") / 1024), "KB")

# --- a plain screenshot of the interface for the top of the README
Image.open(FRAMES[MARKS.get("beforeFrame", 6)]).convert("RGB").resize((1100, round(800 * 1100 / 1320)), Image.LANCZOS) \
     .save("docs/interface.png", optimize=True)
print("docs/interface.png", round(os.path.getsize("docs/interface.png") / 1024), "KB")
