/**
 * Records the README demo GIF by driving the real editor in a headless browser.
 *
 *   npm i playwright && npx playwright install chromium
 *   python -m http.server 8899
 *   node tools/record-demo.mjs
 *   python tools/build-gif.py
 *
 * The demo colours in demo/garden.png with the paint bucket, lifts the colour,
 * drops the editor's own background and opens the save panel. FILLS holds the
 * click points in image pixel coordinates, so a different drawing just needs a
 * different list.
 */
import { chromium } from 'playwright';
import { mkdirSync, rmSync, writeFileSync } from 'fs';

const PICTURE = process.argv[2] || 'demo/garden.png';
const URL = process.env.DEMO_URL || 'http://127.0.0.1:8899/index.html';
const OUT = 'tools/_frames';
const VIEW = { width: 1320, height: 800 };

const FILLS = [
  ['#9fd8f2', 60, 60, 'sky'],
  ['#ffd45e', 820, 106, 'sun'],
  ['#f4fbff', 470, 80, 'cloud'],
  ['#f4fbff', 690, 160, 'cloud'],
  ['#86c96f', 480, 400, 'grass'],
  ['#3f8f4e', 182, 220, 'tree'],
  ['#a9743f', 184, 340, 'trunk'],
  ['#e8679b', 437, 452, 'petals'],
  ['#ffd45e', 400, 452, 'centre'],
  ['#5aa84f', 374, 539, 'leaf'],
  ['#f0924a', 584, 418, 'petals'],
  ['#ffd45e', 552, 418, 'centre'],
  ['#5aa84f', 526, 505, 'leaf'],
  ['#b97ae0', 739, 472, 'petals'],
  ['#ffd45e', 700, 472, 'centre'],
  ['#5aa84f', 674, 559, 'leaf'],
  ['#e0564f', 876, 428, 'petals'],
  ['#ffd45e', 846, 428, 'centre'],
  ['#5aa84f', 820, 515, 'leaf'],
  ['#4e9c5b', 250, 520, 'bush'],
  ['#55b2b8', 108, 530, 'watering can'],
];

rmSync(OUT, { recursive: true, force: true });
mkdirSync(OUT, { recursive: true });

const browser = await chromium.launch({ executablePath: process.env.CHROMIUM_PATH || undefined });
const page = await browser.newPage({ viewport: VIEW, deviceScaleFactor: 1 });
await page.goto(URL);
await page.waitForTimeout(1800);

let n = 0;
const shot = async (count = 1) => {
  for (let i = 0; i < count; i++) await page.screenshot({ path: `${OUT}/${String(n++).padStart(4, '0')}.png` });
};
const blurKey = async k => {
  await page.evaluate(() => document.activeElement && document.activeElement.blur());
  await page.keyboard.press(k);
};

await shot(5);
await page.setInputFiles('#fileIn', PICTURE);
await page.waitForTimeout(900);
const beforeFrame = n;
await shot(8);

const stage = await page.locator('#stage').boundingBox();
async function probe(sx, sy) {
  await page.mouse.move(stage.x + sx, stage.y + sy);
  const [x, y] = (await page.locator('#stPos').textContent()).split(',').map(Number);
  return { x, y };
}
const a = await probe(320, 300), b = await probe(700, 600);
const k = (700 - 320) / (b.x - a.x);
const ox = stage.x + 320 - a.x * k, oy = stage.y + 300 - a.y * k;
const S = (x, y) => [ox + x * k, oy + y * k];

// Colour each region with the paint bucket.
await blurKey('g');
await page.waitForTimeout(400);
await shot(5);
for (const [colour, x, y] of FILLS) {
  await page.locator('#cFore').evaluate((el, c) => {
    el.value = c;
    el.dispatchEvent(new Event('input', { bubbles: true }));
  }, colour);
  await page.mouse.click(...S(x, y));
  await page.waitForTimeout(110);
  await shot();
}
const afterFrame = n;
await shot(8);

// Lift the colour with an adjustment.
for (const v of [120, 140, 155]) {
  await page.locator('#aSat').fill(String(v));
  await page.dispatchEvent('#aSat', 'input');
  await page.waitForTimeout(260);
  await shot(2);
}
await page.locator('#aApply').click();
await page.waitForTimeout(500);
await shot(5);

// Drop the editor's own backdrop, then open the save panel.
await page.evaluate(() => document.activeElement && document.activeElement.blur());
await page.locator('#btnCut').click();
await page.waitForTimeout(1200);
await shot(8);
await page.locator('#btnExport').click();
await page.waitForTimeout(900);
await shot(10);

writeFileSync(`${OUT}/marks.json`, JSON.stringify({ beforeFrame, afterFrame }));
console.log(`captured ${n} frames into ${OUT}/ (before=${beforeFrame}, after=${afterFrame})`);
await browser.close();
