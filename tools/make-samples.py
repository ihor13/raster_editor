#!/usr/bin/env python3
"""Generate the sample images the demo and the README use.

    python tools/make-samples.py

Writes demo/garden.png, a line drawing with closed regions the paint bucket can
fill, and demo/skin.png, a patch of skin with creases for the retouch example.
No photographs and no people are involved.
"""
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

INK = (44, 42, 48)


def union(base, shapes, w=4):
    """Draw one closed outline around a group of overlapping shapes.

    Overlapping circles each leave their own region, so a paint bucket would fill
    only the one under the cursor. Merging them into a single mask and stroking
    the mask's edge gives one region per object instead.
    """
    m = Image.new("L", base.size, 0)
    md = ImageDraw.Draw(m)
    for kind, box in shapes:
        getattr(md, kind)(box, fill=255)
    base.paste((255, 255, 255), (0, 0), m)
    edge = ImageChops.difference(m, m.filter(ImageFilter.MinFilter(2 * w + 1)))
    base.paste(INK, (0, 0), edge)


def garden(path, W=960, H=640):
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    w = 4
    horizon = 360
    d.line([(0, horizon), (W, horizon)], fill=INK, width=w)

    # sun and rays
    d.ellipse([W - 190, 56, W - 90, 156], fill="white", outline=INK, width=w)
    for i in range(12):
        a = i * np.pi / 6
        cx, cy = W - 140, 106
        d.line([(cx + np.cos(a) * 62, cy + np.sin(a) * 62),
                (cx + np.cos(a) * 84, cy + np.sin(a) * 84)], fill=INK, width=3)

    # clouds
    for cx, cy, s in [(170, 112, 1.0), (470, 80, 0.8), (690, 160, 0.62)]:
        union(im, [("ellipse", [cx - 70 * s, cy - 2 * s, cx + 70 * s, cy + 44 * s]),
                   ("ellipse", [cx - 38 * s, cy - 34 * s, cx + 42 * s, cy + 34 * s]),
                   ("ellipse", [cx + 10 * s, cy - 18 * s, cx + 88 * s, cy + 40 * s])], w)

    # tree: trunk first, then one merged canopy
    d.polygon([(158, horizon), (170, 250), (198, 250), (210, horizon)],
              fill="white", outline=INK, width=w)
    union(im, [("ellipse", [110, 142, 254, 286]),
               ("ellipse", [82, 196, 190, 304]),
               ("ellipse", [176, 196, 284, 304]),
               ("ellipse", [124, 214, 244, 322])], w)

    # flowers: one merged rosette, a centre, a stem and a leaf
    for fx, fy, pr in [(400, 452, 32), (552, 418, 28), (700, 472, 34), (846, 428, 26)]:
        d.line([(fx, fy + pr + 4), (fx + 6, H - 56)], fill=INK, width=w)
        petals = []
        for i in range(6):
            a = i * np.pi / 3
            px, py = fx + np.cos(a) * pr * 1.15, fy + np.sin(a) * pr * 1.15
            petals.append(("ellipse", [px - pr * 0.8, py - pr * 0.8, px + pr * 0.8, py + pr * 0.8]))
        union(im, petals, w)
        d.ellipse([fx - pr * 0.58, fy - pr * 0.58, fx + pr * 0.58, fy + pr * 0.58],
                  fill="white", outline=INK, width=w)
        d.ellipse([fx - 54, fy + 70, fx + 2, fy + 104], fill="white", outline=INK, width=w)

    # bush and watering can
    union(im, [("ellipse", [208, 478, 292, 562]),
               ("ellipse", [262, 500, 338, 576]),
               ("ellipse", [166, 508, 240, 582])], w)
    d.rounded_rectangle([58, 470, 164, 566], 10, fill="white", outline=INK, width=w)
    d.polygon([(164, 492), (220, 456), (230, 470), (170, 512)], fill="white", outline=INK, width=w)
    d.arc([80, 430, 144, 494], 180, 360, fill=INK, width=w)

    # fence
    for x in range(0, W, 76):
        d.polygon([(x + 10, 596), (x + 34, 572), (x + 58, 596), (x + 58, H - 8), (x + 10, H - 8)],
                  fill="white", outline=INK, width=w)
    d.line([(0, 612), (W, 612)], fill=INK, width=w)

    im.save(path)
    print("wrote", path, im.size)


def skin(path, W=760, H=420):
    rng = np.random.default_rng(5)
    yy, xx = np.mgrid[0:H, 0:W]

    light = np.clip(1.10 - (((xx - W * 0.35) ** 2 + (yy - H * 0.3) ** 2) ** 0.5) / 1500.0, 0.8, 1.10)
    img = np.zeros((H, W, 3), float)
    for i, base in enumerate((228, 183, 158)):
        img[..., i] = base * light

    blotch = rng.normal(0, 1, (H // 26, W // 26))
    blotch = np.asarray(Image.fromarray(((blotch * .5 + .5) * 255).clip(0, 255).astype(np.uint8))
                        .resize((W, H), Image.BICUBIC), float) / 255.0 - 0.5
    img[..., 0] += blotch * 13
    img[..., 1] += blotch * 9
    img[..., 2] += blotch * 7

    creases = Image.new("L", (W, H), 0)
    c = ImageDraw.Draw(creases)
    for i, oy in enumerate((-70, -24, 26, 76)):
        c.arc([90, H // 2 + oy - 40, W - 90, H // 2 + oy + 40], 196, 344, fill=150 - i * 12, width=6)
    creases = creases.filter(ImageFilter.GaussianBlur(2.2))
    cm = np.asarray(creases, float)[..., None] / 255.0
    img *= (1 - cm * 0.34)
    img[..., 2] -= cm[..., 0] * 12

    for sx, sy, r, st in [(220, 300, 9, .5), (520, 220, 7, .45), (610, 330, 8, .38), (330, 150, 6, .42)]:
        g = np.exp(-(((xx - sx) / r) ** 2 + ((yy - sy) / r) ** 2))[..., None] * st
        img = img * (1 - g * 0.45) + np.array([170., 108., 100.]) * g * 0.45

    fine = rng.normal(0, 1, (H, W))
    fine = np.asarray(Image.fromarray(((fine * .5 + .5) * 255).clip(0, 255).astype(np.uint8))
                      .filter(ImageFilter.GaussianBlur(0.6)), float)[..., None] / 255.0 - 0.5
    img += fine * 17
    img += rng.normal(0, 1.8, (H, W, 3))

    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(path)
    print("wrote", path, (W, H))


if __name__ == "__main__":
    garden("demo/garden.png")
    skin("demo/skin.png")
