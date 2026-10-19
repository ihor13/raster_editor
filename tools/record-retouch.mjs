/**
 * Builds the retouch illustration for the README: a patch of skin before and
 * after the heal brush. Run the same way as record-demo.mjs, then:
 *
 *   python tools/build-retouch.py
 */
import { chromium } from 'playwright';
import { mkdirSync, rmSync, writeFileSync } from 'fs';

const PICTURE = 'demo/skin.png';
const URL = process.env.DEMO_URL || 'http://127.0.0.1:8899/index.html';
const OUT = 'tools/_retouch';
const VIEW = { width: 1320, height: 800 };

// The creases are arcs, so follow the same curve make-samples.py drew:
// centre (380, cy), radii 290 x 40, from 196 to 344 degrees.
const CREASES = [140, 186, 236, 286].map(cy => ({ size: 30, cy }));
const arcPoint = (cy, deg) => {
  const t = deg * Math.PI / 180;
  return [380 + 290 * Math.cos(t), cy + 40 * Math.sin(t)];
};

rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
const page = await browser.newPage({ viewport: VIEW, deviceScaleFactor: 1 });
await page.goto(URL);
await page.waitForTimeout(1800);

// a transparent document the size of the swatch, so nothing else is in frame
await page.locator('.sect', { hasText: 'Document' }).first().locator('.secthead').click();
await page.locator('#impFresh button[data-v="1"]').click();
await page.setInputFiles('#fileIn', PICTURE);
await page.waitForTimeout(1200);

const stage = await page.locator('#stage').boundingBox();
async function probe(sx, sy) {
  await page.mouse.move(stage.x + sx, stage.y + sy);
  const [x, y] = (await page.locator('#stPos').textContent()).split(',').map(Number);
  return { x, y };
}
const a = await probe(300, 260), b = await probe(640, 520);
const k = (640 - 300) / (b.x - a.x);
const ox = stage.x + 300 - a.x * k, oy = stage.y + 260 - a.y * k;
const S = (x, y) => [ox + x * k, oy + y * k];
const rect = {
  x: Math.round(ox - stage.x), y: Math.round(oy - stage.y),
  w: Math.round(760 * k), h: Math.round(420 * k),
  stageX: Math.round(stage.x), stageY: Math.round(stage.y)
};

await page.screenshot({ path: `${OUT}/before.png` });

await page.evaluate(() => document.activeElement && document.activeElement.blur());
await page.keyboard.press('r');
await page.waitForTimeout(300);
await page.locator('#rStr').fill('95');
await page.dispatchEvent('#rStr', 'input');
for (let pass = 0; pass < 2; pass++) {
  for (const c of CREASES) {
    await page.locator('#rSize').fill(String(c.size));
    await page.dispatchEvent('#rSize', 'input');
    const steps = 46;
    const [x0, y0] = arcPoint(c.cy, 196);
    await page.mouse.move(...S(x0, y0));
    await page.mouse.down();
    for (let i = 1; i <= steps; i++) {
      const [px, py] = arcPoint(c.cy, 196 + (344 - 196) * i / steps);
      await page.mouse.move(...S(px, py));
    }
    await page.mouse.up();
    await page.waitForTimeout(120);
  }
}
await page.waitForTimeout(500);
await page.screenshot({ path: `${OUT}/after.png` });
writeFileSync(`${OUT}/rect.json`, JSON.stringify(rect));
console.log('wrote', OUT, JSON.stringify(rect));
await browser.close();
