#!/usr/bin/env python3
"""Compose docs/retouch-detail.png from the frames record-retouch.mjs captured."""
import json, os
from PIL import Image

rect = json.load(open("tools/_retouch/rect.json"))
# rect is stage-relative; the screenshots are of the whole page
x0 = rect["x"] + rect["stageX"]
y0 = rect["y"] + rect["stageY"]
box = (x0, y0, x0 + rect["w"], y0 + rect["h"])
a = Image.open("tools/_retouch/before.png").convert("RGB").crop(box)
b = Image.open("tools/_retouch/after.png").convert("RGB").crop(box)
gap = 12
sheet = Image.new("RGB", (a.width * 2 + gap, a.height), (18, 19, 22))
sheet.paste(a, (0, 0))
sheet.paste(b, (a.width + gap, 0))
sheet = sheet.resize((1000, round(sheet.height * 1000 / sheet.width)), Image.LANCZOS)
os.makedirs("docs", exist_ok=True)
sheet.save("docs/retouch-detail.png", optimize=True)
print("docs/retouch-detail.png", round(os.path.getsize("docs/retouch-detail.png") / 1024), "KB")
