
const puppeteer = require('puppeteer-core');

(async () => {
  const [url, outDir, fpsStr, secsStr, widthStr] = process.argv.slice(2);
  const fps = parseInt(fpsStr, 10), secs = parseInt(secsStr, 10);
  const width = parseInt(widthStr, 10);
  const out = require('path').resolve(outDir);
  const fs = require('fs');
  fs.mkdirSync(out, { recursive: true });

  const browser = await puppeteer.launch({
    executablePath: process.env.GIF_CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    headless: 'new',
    args: ['--no-sandbox', '--disable-gpu', '--hide-scrollbars',
           '--force-color-profile=srgb', '--window-size=' + width + ',800']
  });
  try {
    const page = await browser.newPage();
    await page.setViewport({ width, height: 800, deviceScaleFactor: 1 });
    page.on('pageerror', e => console.error('pageerror:', e.message));
    // console logs from the page (animation bugs often show here)
    page.on('console', m => { if (m.type() === 'error') console.error('page console.error:', m.text()); });

    const errors = [];
    await page.goto(url, { waitUntil: 'load', timeout: 15000 }).catch(e => errors.push('goto: ' + e.message));
    // let the animation warm up before capturing
    await new Promise(r => setTimeout(r, 1200));

    const total = fps * secs;
    const intervalMs = 1000 / fps;
    const t0 = Date.now();
    let written = 0;
    // capture by looping real time so animations run at true speed
    while (written < total && Date.now() - t0 < (secs + 4) * 1000) {
      const frame = Date.now() - t0;
      if (frame >= written * intervalMs) {
        const name = 'f' + String(written).padStart(4, '0') + '.png';
        await page.screenshot({ path: require('path').join(out, name) });
        written++;
      }
      await new Promise(r => setTimeout(r, Math.max(8, Math.floor(intervalMs / 3))));
    }
    console.log('captured ' + written + ' frames');
    if (errors.length) console.error(errors.join('\n'));
  } finally {
    await browser.close();
  }
})().catch(e => { console.error('FATAL', e); process.exit(1); });
