// Real-time capture through the Chrome DevTools Protocol.
// usage: node shot.mjs <chrome> <port> <mode: frames|full> <file.html> <out-prefix>
import { spawn } from 'node:child_process';
import { writeFileSync, mkdtempSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const [chrome, port, mode, html, out] = process.argv.slice(2);
const sleep = ms => new Promise(r => setTimeout(r, ms));
const proc = spawn(chrome, ['--headless', '--no-sandbox', '--hide-scrollbars', '--remote-debugging-port=' + port,
  '--user-data-dir=' + mkdtempSync(join(tmpdir(), 'bv-')), 'about:blank'], { stdio: 'ignore' });
const kill = () => { try { proc.kill('SIGKILL'); } catch {} };
setTimeout(() => { kill(); process.exit(2); }, 90000);

let target;
for (let i = 0; i < 50 && !target; i++) {
  await sleep(200);
  try { target = (await (await fetch(`http://127.0.0.1:${port}/json`)).json()).find(t => t.type === 'page'); } catch {}
}
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r));
let id = 0; const pending = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); if (pending.has(m.id)) { pending.get(m.id)(m.result || {}); pending.delete(m.id); } });
const cdp = (method, params = {}) => new Promise(r => { pending.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });
const grab = async (file, clip) => {
  const r = await cdp('Page.captureScreenshot', Object.assign({ format: 'png' }, clip ? { clip, captureBeyondViewport: true } : {}));
  writeFileSync(file, Buffer.from(r.data, 'base64'));
};

await cdp('Emulation.setDeviceMetricsOverride', { width: 1280, height: mode === 'full' ? 800 : 720, deviceScaleFactor: 1, mobile: false });
await cdp('Page.navigate', { url: 'file://' + html });
await sleep(2000);
if (mode === 'frames') {
  // three moments of the walk, 450ms of real time apart
  for (let i = 0; i < 3; i++) { await grab(`${out}-${i}.png`); await sleep(450); }
} else {
  // scroll the whole page first so scroll-triggered reveals have fired, then capture all of it
  const h = async () => (await cdp('Runtime.evaluate', { expression: 'Math.max(document.documentElement.scrollHeight, document.body ? document.body.scrollHeight : 0)', returnByValue: true })).result.value;
  let height = await h();
  for (let y = 0; y < height; y += 600) { await cdp('Runtime.evaluate', { expression: `window.scrollTo(0, ${y})` }); await sleep(120); }
  await cdp('Runtime.evaluate', { expression: 'window.scrollTo(0, 0)' });
  await sleep(600);
  height = Math.min(await h(), 12000);
  await grab(`${out}.png`, { x: 0, y: 0, width: 1280, height, scale: 1 });
  console.log(height);
}
ws.close(); kill(); process.exit(0);
