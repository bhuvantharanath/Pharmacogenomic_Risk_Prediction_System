// Audit-only driver for a task-owned, isolated-profile Google Chrome over CDP.
//
// Usage: node cdp_agent.mjs <label> <control-port> <debug-port> [--kiosk-printing]
//
// Starts the installed Google Chrome with its own temporary profile (never the
// person's profile), then exposes a loopback-only HTTP control endpoint so each
// step can be issued and inspected individually. Clicks are real CDP input
// events (trusted, with user activation). File uploads use the browser's own
// file-chooser event: the page's click opens the chooser, CDP intercepts the
// chooser and supplies the real file path. Every CDP event of interest is
// appended to events.jsonl. No production code is involved.

import { spawn } from 'node:child_process';
import fs from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const [label, ctlPortArg, dbgPortArg, ...flags] = process.argv.slice(2);
// fileURLToPath, not URL.pathname: the repository path contains spaces, and
// .pathname keeps them percent-encoded (first attempt created a stray
// "%20" directory; receipts kept under failed-attempts/).
const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, label);
fs.mkdirSync(OUT, { recursive: true });
// The disposable Chrome profile lives outside the repository (scratch), so it
// never pollutes evidence or git status; only receipts stay under OUT.
const PROFILE = path.join(process.env.CDP_PROFILE_ROOT || OUT, `profile-${label}`);
const DOWNLOADS = path.join(OUT, 'downloads');
const PRINTS = path.join(OUT, 'print');
for (const d of [PROFILE, DOWNLOADS, PRINTS]) fs.mkdirSync(d, { recursive: true });
const CTL = Number(ctlPortArg);
const DBG = Number(dbgPortArg);
const KIOSK = flags.includes('--kiosk-printing');
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const EVENTS = fs.createWriteStream(path.join(OUT, 'events.jsonl'), { flags: 'a' });
const log = (kind, payload) =>
  EVENTS.write(JSON.stringify({ at: new Date().toISOString(), kind, ...payload }) + '\n');

// Isolated profile preferences: downloads and print-to-PDF land in this task's
// evidence folder; the only print destination on this host is Save as PDF.
const prefsDir = path.join(PROFILE, 'Default');
fs.mkdirSync(prefsDir, { recursive: true });
const prefsFile = path.join(prefsDir, 'Preferences');
if (!fs.existsSync(prefsFile)) {
  fs.writeFileSync(prefsFile, JSON.stringify({
    download: { default_directory: DOWNLOADS, prompt_for_download: false },
    savefile: { default_directory: PRINTS },
    printing: {
      print_preview_sticky_settings: {
        appState: JSON.stringify({
          version: 2,
          recentDestinations: [{ id: 'Save as PDF', origin: 'local', account: '' }],
          selectedDestinationId: 'Save as PDF',
        }),
      },
    },
  }));
}

const argv = [
  `--user-data-dir=${PROFILE}`,
  `--remote-debugging-port=${DBG}`,
  '--remote-allow-origins=http://127.0.0.1',
  '--no-first-run',
  '--no-default-browser-check',
  '--window-size=1280,860',
  // An external actor clicked inside the first, on-screen window (see
  // failed-attempts/ and baseline/). Keep the window off the visible display
  // and stop Chrome throttling it for being occluded, so it still renders.
  ...(flags.includes('--offscreen') ? ['--window-position=1705,1100'] : []),
  '--disable-backgrounding-occluded-windows',
  '--disable-renderer-backgrounding',
  '--disable-background-timer-throttling',
  ...(KIOSK ? ['--kiosk-printing'] : []),
  // No window at all: used after the person closed a visible test window.
  ...(flags.includes('--headless') ? ['--headless=new'] : []),
  'about:blank',
];
const chrome = spawn(CHROME, argv, { stdio: ['ignore', 'pipe', 'pipe'] });
chrome.stdout.on('data', (b) => log('chrome-stdout', { text: b.toString().slice(0, 2000) }));
chrome.stderr.on('data', (b) => log('chrome-stderr', { text: b.toString().slice(0, 2000) }));
chrome.on('exit', (code, signal) => {
  log('chrome-exit', { code, signal });
  fs.writeFileSync(path.join(OUT, 'chrome-exit.json'), JSON.stringify({ code, signal, at: new Date().toISOString() }, null, 1));
});
fs.writeFileSync(path.join(OUT, 'chrome-command.json'), JSON.stringify({
  binary: CHROME, argv, pid: chrome.pid, agent_pid: process.pid, control_port: CTL, debug_port: DBG,
  profile: PROFILE, downloads: DOWNLOADS, print_dir: PRINTS, kiosk_printing: KIOSK,
  started: new Date().toISOString(),
}, null, 1));

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
async function waitForDebugger() {
  for (let i = 0; i < 100; i++) {
    try {
      const r = await fetch(`http://127.0.0.1:${DBG}/json/version`);
      if (r.ok) return await r.json();
    } catch { /* not up yet */ }
    await sleep(200);
  }
  throw new Error('Chrome debugger did not start');
}

class Session {
  constructor(url, name) {
    this.name = name; this.id = 0; this.pending = new Map(); this.handlers = [];
    this.ws = new WebSocket(url);
    this.ready = new Promise((resolve, reject) => {
      this.ws.onopen = resolve; this.ws.onerror = reject;
    });
    this.ws.onmessage = (m) => {
      const msg = JSON.parse(typeof m.data === 'string' ? m.data : m.data.toString());
      if (msg.id && this.pending.has(msg.id)) {
        const { resolve, reject } = this.pending.get(msg.id); this.pending.delete(msg.id);
        msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
      } else if (msg.method) {
        for (const h of this.handlers) h(msg);
      }
    };
  }
  send(method, params = {}) {
    const id = ++this.id;
    this.ws.send(JSON.stringify({ id, method, params }));
    return new Promise((resolve, reject) => {
      this.pending.set(id, { resolve, reject });
      setTimeout(() => { if (this.pending.has(id)) { this.pending.delete(id); reject(new Error(`timeout ${method}`)); } }, 60000);
    });
  }
}

const version = await waitForDebugger();
log('chrome-version', { version });
const browser = new Session(version.webSocketDebuggerUrl, 'browser');
await browser.ready;
const targets = await (await fetch(`http://127.0.0.1:${DBG}/json/list`)).json();
const pageTarget = targets.find((t) => t.type === 'page');
const page = new Session(pageTarget.webSocketDebuggerUrl, 'page');
await page.ready;

const state = { nextUpload: null, uploads: [], downloads: [], network: {}, console: [], fileChoosers: [] };
const API_PREFIX = 'http://127.0.0.1:8000/';
page.handlers.push(async (msg) => {
  const { method, params } = msg;
  if (method === 'Page.fileChooserOpened') {
    const record = { at: new Date().toISOString(), mode: params.mode, backendNodeId: params.backendNodeId, supplied: state.nextUpload };
    state.fileChoosers.push(record); log('file-chooser', record);
    if (state.nextUpload) {
      try {
        await page.send('DOM.setFileInputFiles', { files: [state.nextUpload], backendNodeId: params.backendNodeId });
        state.uploads.push({ ...record, ok: true });
      } catch (e) { state.uploads.push({ ...record, ok: false, error: String(e) }); }
      state.nextUpload = null;
    }
  } else if (method === 'Runtime.consoleAPICalled') {
    const entry = { type: params.type, text: params.args.map((a) => a.value ?? a.description ?? '').join(' ').slice(0, 2000) };
    state.console.push(entry); log('console', entry);
  } else if (method === 'Runtime.exceptionThrown') {
    const entry = { type: 'exception', text: JSON.stringify(params.exceptionDetails).slice(0, 2000) };
    state.console.push(entry); log('console', entry);
  } else if (method === 'Log.entryAdded') {
    const entry = { type: `log-${params.entry.level}`, text: `${params.entry.source}: ${params.entry.text} ${params.entry.url || ''}`.slice(0, 2000) };
    state.console.push(entry); log('console', entry);
  } else if (method === 'Network.requestWillBeSent' && params.request.url.startsWith(API_PREFIX)) {
    state.network[params.requestId] = { url: params.request.url, method: params.request.method, started: new Date().toISOString() };
    log('net-request', { requestId: params.requestId, ...state.network[params.requestId] });
  } else if (method === 'Network.responseReceived' && state.network[params.requestId]) {
    Object.assign(state.network[params.requestId], { status: params.response.status });
    log('net-response', { requestId: params.requestId, status: params.response.status, url: params.response.url });
  } else if (method === 'Network.loadingFinished' && state.network[params.requestId]) {
    const rec = state.network[params.requestId];
    rec.finished = true;
    try {
      const body = await page.send('Network.getResponseBody', { requestId: params.requestId });
      const raw = body.base64Encoded ? Buffer.from(body.body, 'base64') : Buffer.from(body.body, 'utf8');
      const n = String(Object.keys(state.network).indexOf(params.requestId) + 1).padStart(4, '0');
      const file = path.join(OUT, 'browser-received', `${n}-${rec.method.toLowerCase()}-${new URL(rec.url).pathname.replaceAll('/', '') || 'root'}.body`);
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, raw);
      rec.body_file = path.relative(OUT, file);
      const { createHash } = await import('node:crypto');
      rec.body_sha256 = createHash('sha256').update(raw).digest('hex');
      rec.body_bytes = raw.length;
    } catch (e) { rec.body_error = String(e); }
    log('net-finished', { requestId: params.requestId, ...rec });
  } else if (method === 'Network.loadingFailed' && state.network[params.requestId]) {
    Object.assign(state.network[params.requestId], { failed: params.errorText, canceled: params.canceled });
    log('net-failed', { requestId: params.requestId, ...params });
  } else if (method === 'Page.javascriptDialogOpening') {
    log('js-dialog', params);
  }
});
browser.handlers.push((msg) => {
  if (msg.method === 'Browser.downloadWillBegin' || msg.method === 'Browser.downloadProgress') {
    const p = msg.params;
    let rec = state.downloads.find((d) => d.guid === p.guid);
    if (!rec) { rec = { guid: p.guid }; state.downloads.push(rec); }
    Object.assign(rec, p, { last_event: msg.method, at: new Date().toISOString() });
    log('download', { method: msg.method, ...p });
  }
});

await page.send('Page.enable');
await page.send('Runtime.enable');
await page.send('Log.enable');
await page.send('DOM.enable');
await page.send('Network.enable', { maxResourceBufferSize: 50_000_000, maxTotalBufferSize: 200_000_000 });
await page.send('Page.setInterceptFileChooserDialog', { enabled: true });
await page.send('Emulation.setFocusEmulationEnabled', { enabled: true });
await browser.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: DOWNLOADS, eventsEnabled: true });
await browser.send('Browser.grantPermissions', {
  origin: 'http://127.0.0.1:3000',
  permissions: ['clipboardReadWrite', 'clipboardSanitizedWrite'],
});
log('agent-ready', { page: pageTarget.id });

async function evaluate(expression) {
  const r = await page.send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(JSON.stringify(r.exceptionDetails).slice(0, 1500));
  return r.result.value;
}

// Flutter renders to a canvas; its accessibility tree mirrors widgets as DOM
// nodes with labels and geometry, which is how text is located for clicks.
const NODES_JS = `(() => {
  const out = [];
  for (const el of document.querySelectorAll('flt-semantics, flt-semantics *')) {
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) continue;
    const label = (el.getAttribute('aria-label') || '').trim();
    const own = [...el.childNodes].filter(n => n.nodeType === 3).map(n => n.textContent).join(' ').trim();
    const text = label || own;
    if (!text && !el.getAttribute('role')) continue;
    out.push({ id: el.id || '', tag: el.tagName.toLowerCase(), role: el.getAttribute('role') || '', text,
      disabled: el.getAttribute('aria-disabled') === 'true', x: Math.round(r.x), y: Math.round(r.y),
      w: Math.round(r.width), h: Math.round(r.height) });
  }
  return out;
})()`;

async function click(x, y, opts = {}) {
  const base = { x, y, button: 'left', clickCount: 1, modifiers: opts.modifiers || 0 };
  await page.send('Input.dispatchMouseEvent', { type: 'mouseMoved', x, y });
  await page.send('Input.dispatchMouseEvent', { type: 'mousePressed', ...base });
  await page.send('Input.dispatchMouseEvent', { type: 'mouseReleased', ...base });
}

async function handle(cmd) {
  switch (cmd.op) {
    case 'cdp': return await (cmd.target === 'browser' ? browser : page).send(cmd.method, cmd.params || {});
    case 'eval': return await evaluate(cmd.expr);
    case 'navigate': return await page.send('Page.navigate', { url: cmd.url });
    case 'semantics': return await evaluate(`(() => { const p = document.querySelector('flt-semantics-placeholder'); if (p) { p.click(); return 'enabled'; } return 'no-placeholder'; })()`);
    case 'nodes': return await evaluate(NODES_JS);
    case 'click': await click(cmd.x, cmd.y); return { clicked: [cmd.x, cmd.y] };
    case 'click_text': {
      const nodes = await evaluate(NODES_JS);
      const want = cmd.text.toLowerCase();
      const hits = nodes.filter((n) => (cmd.exact ? n.text.toLowerCase() === want : n.text.toLowerCase().includes(want)) && (!cmd.role || n.role === cmd.role));
      const node = hits[cmd.nth || 0];
      if (!node) return { clicked: null, candidates: hits.length };
      const x = node.x + Math.round(node.w / 2), y = node.y + Math.round(node.h / 2);
      await click(x, y);
      return { clicked: node, at: [x, y], candidates: hits.length };
    }
    case 'type': await page.send('Input.insertText', { text: cmd.text }); return { typed: cmd.text.length };
    case 'key': {
      const mods = cmd.modifiers || 0;
      const desc = { key: cmd.key, code: cmd.code || cmd.key, windowsVirtualKeyCode: cmd.vk || 0, modifiers: mods };
      if (cmd.commands) desc.commands = cmd.commands;
      await page.send('Input.dispatchKeyEvent', { type: 'rawKeyDown', ...desc });
      await page.send('Input.dispatchKeyEvent', { type: 'keyUp', ...desc });
      return { key: cmd.key };
    }
    case 'wheel': await page.send('Input.dispatchMouseEvent', { type: 'mouseWheel', x: cmd.x, y: cmd.y, deltaX: 0, deltaY: cmd.dy }); return { wheel: cmd.dy };
    case 'screenshot': {
      const shot = await page.send('Page.captureScreenshot', { format: 'png' });
      const file = path.join(OUT, 'screens', cmd.name + '.png');
      fs.mkdirSync(path.dirname(file), { recursive: true });
      fs.writeFileSync(file, Buffer.from(shot.data, 'base64'));
      return { file };
    }
    case 'set_upload': state.nextUpload = cmd.path; return { armed: cmd.path };
    case 'viewport':
      return await page.send('Emulation.setDeviceMetricsOverride', { width: cmd.w, height: cmd.h, deviceScaleFactor: 1, mobile: !!cmd.mobile });
    case 'clear_viewport': return await page.send('Emulation.clearDeviceMetricsOverride');
    case 'state': return { uploads: state.uploads, downloads: state.downloads, fileChoosers: state.fileChoosers, network: state.network, console: state.console.slice(-(cmd.console || 30)) };
    case 'bring_to_front': return await page.send('Page.bringToFront');
    case 'quit': {
      try { await browser.send('Browser.close'); } catch { /* closing */ }
      setTimeout(() => process.exit(0), 1500);
      return { quitting: true };
    }
    default: throw new Error(`unknown op ${cmd.op}`);
  }
}

http.createServer((req, res) => {
  let body = '';
  req.on('data', (c) => { body += c; });
  req.on('end', async () => {
    let cmd = {};
    try {
      cmd = JSON.parse(body || '{}');
      const result = await handle(cmd);
      log('command', { cmd, ok: true });
      res.writeHead(200, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ ok: true, result }));
    } catch (e) {
      log('command', { cmd, ok: false, error: String(e) });
      res.writeHead(500, { 'content-type': 'application/json' });
      res.end(JSON.stringify({ ok: false, error: String(e) }));
    }
  });
}).listen(CTL, '127.0.0.1', () => log('control-listening', { port: CTL }));
