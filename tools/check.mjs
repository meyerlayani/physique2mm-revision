// Browser check of the site (author tool). Usage: node tools/check.mjs [chapter ...] [--shots DIR] [--all]
// Serves the repo on a local port, opens each chapter, verifies images / KaTeX, answers every question.
import { createServer } from 'http';
import { readFile } from 'fs/promises';
import { extname, join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { chromium } = require('playwright');

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const TYPES = { '.html': 'text/html', '.js': 'text/javascript', '.css': 'text/css', '.json': 'application/json',
  '.png': 'image/png', '.woff2': 'font/woff2', '.svg': 'image/svg+xml' };
const args = process.argv.slice(2);
const shots = args.includes('--shots') ? args[args.indexOf('--shots') + 1] : null;
const server = createServer(async (req, res) => {
  const p = decodeURIComponent(new URL(req.url, 'http://x').pathname);
  try {
    const body = await readFile(join(ROOT, p === '/' ? 'index.html' : p));
    res.writeHead(200, { 'content-type': TYPES[extname(p)] || 'application/octet-stream' }); res.end(body);
  } catch { res.writeHead(404); res.end('nf'); }
}).listen(0);
const base = `http://127.0.0.1:${server.address().port}/`;
const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 390, height: 844 } });
const errors = [];
page.on('pageerror', e => errors.push('pageerror ' + e.message));
page.on('response', r => { if (r.status() >= 400) errors.push(`${r.status()} ${r.url()}`); });

const chapters = JSON.parse(await readFile(join(ROOT, 'data/chapters.json')));
let todo = args.filter(a => /^\d+$/.test(a) && args[args.indexOf(a) - 1] !== '--shots').map(Number);
if (!todo.length) todo = chapters.chapters.filter(c => c.ids.length).map(c => c.n);

await page.goto(base + 'index.html');
await page.evaluate(() => localStorage.clear());
for (const c of todo) {
  for (const lang of ['fr', 'he']) {
    await page.goto(`${base}chapter.html?c=${c}`);
    await page.evaluate(l => localStorage.setItem('p2mm-lang', l), lang);
    await page.reload();
    await page.waitForSelector('.question');
    const qs = await page.$$('.question');
    for (const q of qs) {
      const opts = await q.$$('.opt');
      await opts[Math.floor(Math.random() * opts.length)].click();
    }
    await page.waitForTimeout(300);
    // force lazy images to load
    await page.evaluate(async () => {
      for (const img of document.images) { img.loading = 'eager'; }
      await Promise.all([...document.images].map(i => i.complete ? 0 : new Promise(r => { i.onload = i.onerror = r; })));
    });
    const r = await page.evaluate(() => ({
      broken: [...document.images].filter(i => !i.naturalWidth).map(i => i.src),
      katexErr: [...document.querySelectorAll('.katex-error')].map(e => e.title || e.textContent).slice(0, 5),
      rawDollar: [...document.querySelectorAll('.lesson, .corr')].filter(e => e.offsetParent && /\$[^$]+\$/.test(e.innerText)).length,
      missingCorr: [...document.querySelectorAll('.corr')].filter(e => /not available/.test(e.textContent)).length,
      overflowX: document.documentElement.scrollWidth > window.innerWidth + 1,
      n: document.querySelectorAll('.question').length,
      header: document.getElementById('ch-detail').textContent,
    }));
    console.log(`ch${c} [${lang}]`, JSON.stringify(r));
    if (shots) await page.screenshot({ path: `${shots}/ch${c}-${lang}.png`, fullPage: true });
  }
}
await page.goto(base + 'index.html');
await page.waitForSelector('.chapter');
console.log('home:', await page.$eval('#global-detail', e => e.textContent), await page.$eval('#global-pct', e => e.textContent));
if (shots) await page.screenshot({ path: `${shots}/home.png`, fullPage: true });
console.log('errors:', errors.length ? errors : 'none');
await browser.close(); server.close();
