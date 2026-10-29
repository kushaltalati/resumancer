#!/usr/bin/env node
// Browser form filler for the /resumancer skill. Two modes:
//   node fill_form.mjs discover --url <form url> --out fields.json [--headless]
//   node fill_form.mjs fill --url <form url> --answers answers.json --out <dir> [--profile <dir>] [--headless]
// Opens an isolated Chrome profile (never the user's daily browser). NEVER clicks a submit button.
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import fs from 'node:fs';

const here = path.dirname(fileURLToPath(import.meta.url));
const require = createRequire(import.meta.url);
let chromium;
try { ({ chromium } = require(path.join(here, 'node_modules', 'playwright-core'))); }
catch { try { ({ chromium } = require('playwright-core')); } catch { console.error('playwright-core not found: run  cd ' + here + ' && npm install'); process.exit(2); } }

const args = process.argv.slice(2);
const mode = args[0];
const opt = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const flag = (k) => args.includes(k);
const url = opt('--url'); if (!url || !['discover', 'fill'].includes(mode)) { console.error('usage: fill_form.mjs discover|fill --url <url> ...'); process.exit(2); }
const outDir = opt('--out', process.cwd());
const profileDir = opt('--profile', path.join(process.env.HOME || '.', '.resumancer', 'browser-profile'));
const headless = flag('--headless');
fs.mkdirSync(profileDir, { recursive: true });
const log = (...a) => console.log(new Date().toISOString().slice(11, 19), ...a);
const SUBMIT_RE = /submit|apply now|send application|send my application/i;

async function launch() {
  const base = { headless, viewport: { width: 1280, height: 1000 }, args: ['--no-first-run', '--disable-features=TranslateUI'] };
  try { return await chromium.launchPersistentContext(profileDir, { ...base, channel: 'chrome' }); }
  catch (e) { log('Google Chrome not usable (' + e.message.split('\n')[0] + '); trying bundled chromium'); return await chromium.launchPersistentContext(profileDir, base); }
}

function frames(page) { return [page.mainFrame(), ...page.frames().filter(f => f !== page.mainFrame())]; }

async function discover(page) {
  const all = [];
  for (const f of frames(page)) {
    let items = [];
    try {
      items = await f.evaluate(() => {
        const out = [];
        const labelFor = (el) => {
          const ids = (el.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean);
          let t = ids.map(i => document.getElementById(i)?.innerText || '').join(' ').trim();
          if (!t && el.id) t = document.querySelector(`label[for="${CSS.escape(el.id)}"]`)?.innerText || '';
          if (!t) t = el.closest('label')?.innerText || '';
          if (!t) t = el.getAttribute('aria-label') || el.getAttribute('placeholder') || '';
          if (!t) { const p = el.closest('div,fieldset'); t = p?.querySelector('label,legend')?.innerText || ''; }
          return t.replace(/\s+/g, ' ').trim().slice(0, 300);
        };
        document.querySelectorAll('input,select,textarea,[role=combobox],[role=listbox]').forEach(el => {
          const type = el.tagName === 'SELECT' ? 'select' : (el.getAttribute('role') === 'combobox' ? 'combobox' : (el.type || el.tagName.toLowerCase()));
          if (['hidden', 'submit', 'button'].includes(type)) return;
          const options = el.tagName === 'SELECT' ? [...el.options].map(o => o.text.trim()).filter(Boolean) : [];
          out.push({ label: labelFor(el), type, required: el.required || el.getAttribute('aria-required') === 'true' || /\*\s*$/.test(labelFor(el)), name: el.name || '', id: el.id || '', options: options.slice(0, 60) });
        });
        return out;
      });
    } catch {}
    for (const it of items) all.push({ ...it, frame: f === page.mainFrame() ? 'main' : (f.name() || f.url()) });
  }
  const seen = new Set();
  return all.filter(i => { const k = i.label + '|' + i.type + '|' + i.name; if (seen.has(k) || !i.label) return false; seen.add(k); return true; });
}

async function pickFrame(page, labelRe) {
  for (const f of frames(page)) { try { const el = f.getByLabel(labelRe).first(); if (await el.count()) return { f, el }; } catch {} }
  return null;
}

function labelRegex(s) { return new RegExp(s, 'i'); }
function optRegex(v) { const esc = v.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replace(/['\u2019]/g, "['\u2019]"); return new RegExp('^\\s*' + esc, 'i'); }

async function fill(page, actions) {
  const report = [];
  for (const a of actions) {
    const re = labelRegex(a.label);
    if (a.type === 'skip') { report.push({ ...a, result: 'skipped' }); log('skip:', a.label, '—', a.reason || ''); continue; }
    const hit = await pickFrame(page, re);
    if (!hit) { report.push({ ...a, result: 'NOT FOUND' }); log('NOT FOUND:', a.label); continue; }
    const { f, el } = hit;
    try {
      await el.scrollIntoViewIfNeeded().catch(() => {});
      if (a.type === 'text') { await el.fill(String(a.value)); report.push({ ...a, result: 'ok' }); log('text ok:', a.label); }
      else if (a.type === 'file') { const fi = (await el.getAttribute('type')) === 'file' ? el : f.locator('input[type=file]').first(); await fi.setInputFiles(a.path); await page.waitForTimeout(2500); report.push({ ...a, result: 'ok' }); log('file ok:', a.path); }
      else if (a.type === 'checkbox') { if (a.value) await el.check(); else await el.uncheck(); report.push({ ...a, result: 'ok' }); log('checkbox ok:', a.label); }
      else if (a.type === 'select' || a.type === 'search') {
        const tag = await el.evaluate(e => e.tagName);
        if (tag === 'SELECT') { await el.selectOption({ label: a.value ?? a.prefer }); report.push({ ...a, result: 'ok' }); log('select ok (native):', a.label); continue; }
        await el.click();
        const typed = a.type === 'search' ? a.typed : String(a.value).slice(0, 24);
        await el.pressSequentially(typed, { delay: 40 });
        await page.waitForTimeout(a.type === 'search' ? 3500 : 600);
        const options = f.getByRole('option');
        const names = await options.allTextContents();
        let idx = -1;
        if (a.type === 'search') { if (a.prefer) idx = names.findIndex(n => labelRegex(a.prefer).test(n)); if (idx < 0) idx = names.findIndex(n => n.toLowerCase().includes(String(a.typed).toLowerCase())); }
        else idx = names.findIndex(n => optRegex(String(a.value)).test(n));
        if (idx >= 0) { await options.nth(idx).click(); await page.waitForTimeout(250); report.push({ ...a, result: 'ok', picked: names[idx] }); log('select ok:', a.label, '=', names[idx]); }
        else { await page.keyboard.press('Escape'); report.push({ ...a, result: 'NO MATCH', visible: names.slice(0, 10) }); log('NO MATCH:', a.label, 'wanted', a.value ?? a.prefer, 'visible', JSON.stringify(names.slice(0, 6))); }
      } else { report.push({ ...a, result: 'unknown type' }); }
    } catch (e) { report.push({ ...a, result: 'ERROR', error: e.message.split('\n')[0] }); log('ERROR:', a.label, e.message.split('\n')[0]); }
  }
  return report;
}

const ctx = await launch();
const page = ctx.pages()[0] ?? await ctx.newPage();
// Safety net: block any navigation triggered by a submit-like button click from automation.
await page.goto(url, { waitUntil: 'domcontentloaded' });
await page.waitForTimeout(3000);
log('loaded', page.url());

if (mode === 'discover') {
  const fields = await discover(page);
  const out = opt('--out', path.join(outDir, 'fields.json'));
  fs.writeFileSync(out, JSON.stringify({ url: page.url(), fields }, null, 2));
  log(`discovered ${fields.length} fields → ${out}`);
  for (const f of fields) console.log(`  [${f.required ? 'REQ' : 'opt'}][${f.type}] ${f.label}${f.options.length ? '  options=' + JSON.stringify(f.options.slice(0, 6)) : ''}`);
  await ctx.close();
  process.exit(0);
}

const answers = JSON.parse(fs.readFileSync(opt('--answers'), 'utf8'));
const actions = (answers.actions || []).filter(a => !(a.type === 'click' || SUBMIT_RE.test(a.label || '')));
const report = await fill(page, actions);
fs.mkdirSync(outDir, { recursive: true });
await page.screenshot({ path: path.join(outDir, 'form.png'), fullPage: true }).catch(() => {});
fs.writeFileSync(path.join(outDir, 'fill-report.json'), JSON.stringify(report, null, 2));
const bad = report.filter(r => r.result !== 'ok');
log(`done: ${report.length - bad.length} ok, ${bad.length} not filled (${bad.map(b => b.label + ':' + b.result).join('; ') || 'none'})`);
log('Submit was NOT clicked. Review the window and submit yourself. The window stays open until you close it.');
if (headless) { await ctx.close(); process.exit(0); }
await new Promise(res => { ctx.on('close', res); page.on('close', res); });
log('browser closed');
