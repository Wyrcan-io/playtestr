import { mkdirSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';

const endpoint = process.argv[2] || 'http://127.0.0.1:9222';
const site = (process.argv[3] || 'http://127.0.0.1:1313/playtestr/').replace(/\/$/, '');
const screenshots = resolve(process.argv[4] || '.cache/site-browser');
mkdirSync(screenshots, { recursive: true });

const targets = await fetch(`${endpoint}/json`).then((response) => response.json());
const page = targets.find((target) => target.type === 'page');
if (!page) throw new Error('No browser page target is available');
const socket = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolveOpen, reject) => { socket.addEventListener('open', resolveOpen, { once: true }); socket.addEventListener('error', reject, { once: true }); });
let sequence = 0;
const pending = new Map();
const eventWaiters = new Map();
socket.addEventListener('message', ({ data }) => {
  const message = JSON.parse(data);
  if (message.id && pending.has(message.id)) {
    const { resolveCall, rejectCall } = pending.get(message.id); pending.delete(message.id);
    if (message.error) rejectCall(new Error(message.error.message)); else resolveCall(message.result);
  }
  if (message.method && eventWaiters.has(message.method)) {
    for (const resolveEvent of eventWaiters.get(message.method)) resolveEvent(message.params);
    eventWaiters.delete(message.method);
  }
});
const call = (method, params = {}) => new Promise((resolveCall, rejectCall) => {
  const id = ++sequence; pending.set(id, { resolveCall, rejectCall }); socket.send(JSON.stringify({ id, method, params }));
});
const event = (method) => new Promise((resolveEvent) => {
  const waiters = eventWaiters.get(method) || []; waiters.push(resolveEvent); eventWaiters.set(method, waiters);
});
const evaluate = async (expression) => (await call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })).result.value;
const navigate = async (url) => { const loaded = event('Page.loadEventFired'); await call('Page.navigate', { url }); await loaded; };

await call('Page.enable');
await call('Runtime.enable');
await call('Accessibility.enable');
await call('Network.enable');
await call('Page.addScriptToEvaluateOnNewDocument', { source: `
  window.__playtestrVitals = { lcp: 0, cls: 0 };
  try { new PerformanceObserver((list) => { const entries = list.getEntries(); const last = entries[entries.length - 1]; if (last) window.__playtestrVitals.lcp = last.renderTime || last.startTime || 0; }).observe({ type: 'largest-contentful-paint', buffered: true }); } catch (_) {}
  try { new PerformanceObserver((list) => { for (const entry of list.getEntries()) if (!entry.hadRecentInput) window.__playtestrVitals.cls += entry.value; }).observe({ type: 'layout-shift', buffered: true }); } catch (_) {}
` });

const routes = ['', 'download/', 'docs/', 'docs/installation/', 'docs/writing-tests/', 'docs/snapshots/', 'docs/troubleshooting/', 'docs/spec-v1/', 'docs/report-v1/', 'docs/compatibility/', 'docs/platform-evidence/', 'docs/terminal-compatibility/', 'examples/', 'releases/', 'releases/v0.1.0/', 'support/', 'trials/', 'does-not-exist/'];
const widths = [320, 375, 768, 1440];
const failures = [];
for (const width of widths) {
  await call('Emulation.setDeviceMetricsOverride', { width, height: width < 700 ? 812 : 1000, deviceScaleFactor: 1, mobile: width < 700 });
  for (const route of routes) {
    await navigate(`${site}/${route}`);
    const state = await evaluate(`(() => ({
      title: document.title,
      h1: document.querySelectorAll('h1').length,
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      skip: Boolean(document.querySelector('.skip[href="#main"]')),
      unnamed: [...document.querySelectorAll('a,button,input')].filter((node) => !(node.getAttribute('aria-label') || node.textContent.trim() || node.getAttribute('placeholder'))).length,
      navVisible: getComputedStyle(document.querySelector('.nav-toggle')).display !== 'none',
      offenders: [...document.querySelectorAll('body *')].filter((node) => { const rect = node.getBoundingClientRect(); return rect.right > document.documentElement.clientWidth + 1 || rect.left < -1; }).slice(0, 6).map((node) => node.tagName.toLowerCase() + '.' + (node.className || '') + ':' + Math.round(node.getBoundingClientRect().left) + '..' + Math.round(node.getBoundingClientRect().right))
    }))()`);
    const label = `${width}px ${route || 'home'}`;
    if (!state.title) failures.push(`${label}: empty title`);
    if (state.h1 !== 1) failures.push(`${label}: expected one h1, found ${state.h1}`);
    if (state.overflow > 1) failures.push(`${label}: horizontal overflow ${state.overflow}px (${state.offenders.join(', ')})`);
    if (!state.skip) failures.push(`${label}: missing skip link`);
    if (state.unnamed) failures.push(`${label}: ${state.unnamed} unnamed controls or links`);
    if (width <= 375 && !state.navVisible) failures.push(`${label}: mobile navigation toggle is hidden`);
  }
}

await call('Emulation.setDeviceMetricsOverride', { width: 375, height: 812, deviceScaleFactor: 1, mobile: true });
await navigate(`${site}/`);
const mobileNav = await evaluate(`(() => { const button = document.querySelector('.nav-toggle'); button.click(); return { expanded: button.getAttribute('aria-expanded'), visible: getComputedStyle(document.querySelector('#site-nav')).display }; })()`);
if (mobileNav.expanded !== 'true' || mobileNav.visible === 'none') failures.push('mobile navigation does not open from its button');
await evaluate(`new Promise((resolve) => { const done = () => resolve(document.querySelector('[data-demo-provenance]').textContent); if (document.querySelector('[data-demo-provenance]').textContent.includes('source')) done(); else setTimeout(done, 1200); })`);
const demo = await evaluate(`(() => {
  document.querySelector('[data-scenario="failure"]').click();
  const next = document.querySelector('[data-demo-action="next"]'); next.click(); next.click(); next.click();
  document.querySelector('[data-evidence="diff"]').click();
  return { result: document.querySelector('[data-demo-result]').textContent, diff: document.querySelector('[data-evidence-output]').textContent, hidden: document.querySelector('[data-evidence-panel]').hidden };
})()`);
if (demo.hidden || !demo.result.includes('snapshot_mismatch') || !demo.diff.includes('Preview deployed successfully.')) failures.push('interactive failure scenario did not expose the verified diff');

await navigate(`${site}/docs/`);
const search = await evaluate(`new Promise((resolve) => {
  const input = document.querySelector('#docs-search'); input.value = 'expect_not'; document.querySelector('[data-search-form]').requestSubmit();
  const check = () => { const status = document.querySelector('[data-search-status]').textContent; if (!status.includes('Searching')) resolve({ status, count: document.querySelectorAll('[data-search-results] li').length }); else setTimeout(check, 25); }; check();
})`);
if (!search.count || !search.status.includes('result')) failures.push('documentation search did not find expect_not');

await call('Emulation.setEmulatedMedia', { features: [{ name: 'prefers-reduced-motion', value: 'reduce' }] });
await navigate(`${site}/`);
await evaluate(`new Promise((resolve) => setTimeout(resolve, 100))`);
const reduced = await evaluate(`(() => { document.querySelector('[data-demo-action="play"]').click(); return document.querySelector('[data-demo-progress]').textContent; })()`);
if (reduced !== '6 / 6') failures.push(`reduced-motion playback did not move directly to the final state: ${reduced}`);
await call('Emulation.setEmulatedMedia', { features: [] });

await call('Emulation.setScriptExecutionDisabled', { value: true });
await navigate(`${site}/examples/`);
const noScript = await evaluate(`({ transcript: document.querySelector('[data-demo-screen]')?.textContent.includes('mission control'), note: Boolean(document.querySelector('.noscript-note')) })`);
if (!noScript.transcript || !noScript.note) failures.push('JavaScript-disabled example lacks its static transcript or explanation');
await call('Emulation.setScriptExecutionDisabled', { value: false });

await call('Emulation.setDeviceMetricsOverride', { width: 375, height: 812, deviceScaleFactor: 1, mobile: true });
await call('Network.emulateNetworkConditions', { offline: false, latency: 150, downloadThroughput: 200000, uploadThroughput: 93750, connectionType: 'cellular3g' });
await call('Emulation.setCPUThrottlingRate', { rate: 4 });
await navigate(`${site}/`);
await evaluate(`new Promise((resolve) => setTimeout(resolve, 1600))`);
const vitals = await evaluate(`window.__playtestrVitals`);
if (vitals.lcp > 2500) failures.push(`mobile lab LCP exceeds 2.5s: ${Math.round(vitals.lcp)}ms`);
if (vitals.cls > 0.1) failures.push(`mobile lab CLS exceeds 0.1: ${vitals.cls.toFixed(3)}`);
await call('Network.emulateNetworkConditions', { offline: false, latency: 0, downloadThroughput: -1, uploadThroughput: -1, connectionType: 'none' });
await call('Emulation.setCPUThrottlingRate', { rate: 1 });

for (const [name, width, route] of [['home-1440', 1440, ''], ['home-375', 375, ''], ['docs-1440', 1440, 'docs/'], ['docs-375', 375, 'docs/']]) {
  await call('Emulation.setDeviceMetricsOverride', { width, height: width < 700 ? 812 : 1000, deviceScaleFactor: 1, mobile: width < 700 });
  await navigate(`${site}/${route}`);
  await evaluate('window.scrollTo(0, 0)');
  const capture = await call('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
  writeFileSync(resolve(screenshots, `${name}.png`), Buffer.from(capture.data, 'base64'));
}

const tree = await call('Accessibility.getFullAXTree');
const unnamedInteractive = tree.nodes.filter((node) => ['button', 'link'].includes(node.role?.value) && !node.name?.value).length;
if (unnamedInteractive) failures.push(`accessibility tree contains ${unnamedInteractive} unnamed links/buttons on docs page`);
socket.close();

if (failures.length) {
  console.error(`Browser validation failed (${failures.length}):\n- ${failures.join('\n- ')}`);
  process.exit(1);
}
console.log(`Browser validation passed: ${routes.length} routes at ${widths.join(', ')}px; search, fallbacks, interactive evidence, and accessibility names verified; mobile lab LCP ${Math.round(vitals.lcp)}ms, CLS ${vitals.cls.toFixed(3)}.`);
