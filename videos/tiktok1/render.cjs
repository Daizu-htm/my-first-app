// index.html の renderFrame(f) を1枚ずつ撮影する。使い方: node render.cjs <開始> <終了> <出力先> [間隔]
const { chromium } = require('playwright');
const path = require('path');

(async () => {
  const [start, end, outDir, stride = '1'] = process.argv.slice(2);
  const browser = await chromium.launch({
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
  });
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  page.on('pageerror', (e) => { console.error('pageerror', e.message); process.exit(1); });
  await page.goto('file://' + path.join(__dirname, 'index.html'));
  await page.evaluate(() => document.fonts.ready);
  for (let f = Number(start); f < Number(end); f += Number(stride)) {
    await page.evaluate((n) => window.renderFrame(n), f);
    await page.screenshot({ path: path.join(outDir, String(f).padStart(5, '0') + '.jpg'), type: 'jpeg', quality: 95 });
  }
  await browser.close();
})();
