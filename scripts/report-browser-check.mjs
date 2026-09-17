import { pathToFileURL } from 'node:url';
import { resolve } from 'node:path';

const endpoint = process.argv[2] || 'http://127.0.0.1:9222';
const reportURL = pathToFileURL(resolve(process.argv[3] || 'artifacts/report.html')).href;
const targets = await fetch(`${endpoint}/json`).then((response) => response.json());
const page = targets.find((target) => target.type === 'page');
if (!page) throw new Error('No browser page target is available');

const socket = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((resolveOpen, reject) => {
  socket.addEventListener('open', resolveOpen, { once: true });
  socket.addEventListener('error', reject, { once: true });
});
let sequence = 0;
const pending = new Map();
const eventWaiters = new Map();
const requests = [];
socket.addEventListener('message', ({ data }) => {
  const message = JSON.parse(data);
  if (message.id && pending.has(message.id)) {
    const { resolveCall, rejectCall } = pending.get(message.id);
    pending.delete(message.id);
    if (message.error) rejectCall(new Error(message.error.message)); else resolveCall(message.result);
  }
  if (message.method === 'Network.requestWillBeSent') requests.push(message.params.request.url);
  if (message.method && eventWaiters.has(message.method)) {
    for (const resolveEvent of eventWaiters.get(message.method)) resolveEvent(message.params);
    eventWaiters.delete(message.method);
  }
});
const call = (method, params = {}) => new Promise((resolveCall, rejectCall) => {
  const id = ++sequence;
  pending.set(id, { resolveCall, rejectCall });
  socket.send(JSON.stringify({ id, method, params }));
});
const event = (method) => new Promise((resolveEvent) => {
  const waiters = eventWaiters.get(method) || [];
  waiters.push(resolveEvent);
  eventWaiters.set(method, waiters);
});
const evaluate = async (expression) => (await call('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true })).result.value;
const navigate = async () => {
  const loaded = event('Page.loadEventFired');
  await call('Page.navigate', { url: reportURL });
  await loaded;
};

await call('Page.enable');
await call('Runtime.enable');
await call('Network.enable');
await call('Accessibility.enable');
const failures = [];

for (const width of [375, 1440]) {
  await call('Emulation.setDeviceMetricsOverride', { width, height: width === 375 ? 812 : 1000, deviceScaleFactor: 1, mobile: width === 375 });
  await navigate();
  const state = await evaluate(`(() => {
    const rgb = (value) => value.match(/[\\d.]+/g).slice(0,3).map(Number).map((channel) => channel / 255).map((channel) => channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4);
    const luminance = (value) => rgb(value).reduce((sum, channel, index) => sum + channel * [.2126,.7152,.0722][index], 0);
    const contrast = (node) => { const style = getComputedStyle(node); const a = luminance(style.color); const b = luminance(style.backgroundColor); return (Math.max(a,b)+.05)/(Math.min(a,b)+.05); };
    const terminal = document.querySelector('.terminal');
    const diff = document.querySelector('.diff');
    const firstFailure = document.querySelector('.failure-nav a');
    return {
      h1: document.querySelectorAll('h1').length,
      pageOverflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      failures: document.querySelectorAll('.failure-nav a').length,
      firstTarget: firstFailure?.getAttribute('href'),
      firstStep: document.querySelector('.result')?.textContent.includes('First failing step'),
      terminalPre: terminal && getComputedStyle(terminal).whiteSpace === 'pre' && getComputedStyle(terminal).fontFamily.toLowerCase().includes('mono'),
      paneScrollable: terminal && ['auto','scroll'].includes(getComputedStyle(terminal).overflowX),
      diffHighlights: Boolean(diff?.querySelector('.added')) && Boolean(diff?.querySelector('.removed')),
      scriptCount: document.scripts.length,
      external: [...document.querySelectorAll('[href],[src]')].map((node) => node.href || node.src).filter((url) => /^https?:/i.test(url)),
      skip: Boolean(document.querySelector('.skip[href="#main"]')),
      contrast: contrast(document.body),
      diffContrast: [...document.querySelectorAll('.diff-line.added,.diff-line.removed')].map(contrast)
    };
  })()`);
  const label = `${width}px`;
  if (state.h1 !== 1) failures.push(`${label}: expected one h1`);
  if (state.pageOverflow > 1) failures.push(`${label}: page overflows horizontally by ${state.pageOverflow}px`);
  if (!state.failures || !state.firstTarget || !state.firstStep) failures.push(`${label}: first failure and failing step are not immediately navigable`);
  if (!state.terminalPre || !state.paneScrollable) failures.push(`${label}: terminal pane does not retain aligned, internally scrollable text`);
  if (!state.diffHighlights) failures.push(`${label}: diff additions/removals are not visibly classified`);
  if (state.scriptCount || state.external.length) failures.push(`${label}: report contains active or external resources`);
  if (!state.skip) failures.push(`${label}: skip link is missing`);
  if (state.contrast < 4.5) failures.push(`${label}: body contrast is ${state.contrast.toFixed(2)}:1`);
  if (state.diffContrast.some((value) => value < 4.5)) failures.push(`${label}: a highlighted diff row is below 4.5:1 contrast`);
}

await call('Emulation.setDeviceMetricsOverride', { width: 375, height: 812, deviceScaleFactor: 1, mobile: true });
await navigate();
await call('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Tab', code: 'Tab' });
await call('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Tab', code: 'Tab' });
const firstFocus = await evaluate('document.activeElement?.className || document.activeElement?.tagName');
if (!String(firstFocus).includes('skip')) failures.push(`keyboard: first focus is ${firstFocus}, not the skip link`);
await call('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Enter', code: 'Enter' });
await call('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Enter', code: 'Enter' });
const skipped = await evaluate('location.hash');
if (skipped !== '#main') failures.push(`keyboard: skip link did not navigate to #main (${skipped})`);

await call('Emulation.setScriptExecutionDisabled', { value: true });
await navigate();
const noScript = await evaluate(`({ heading: document.querySelector('h1')?.textContent, failures: document.querySelectorAll('.failure-nav a').length, screen: Boolean(document.querySelector('.terminal')) })`);
await call('Emulation.setScriptExecutionDisabled', { value: false });
if (noScript.heading !== 'Run diagnosis' || !noScript.failures || !noScript.screen) failures.push('JavaScript-disabled report is not fully usable');

const remoteRequests = requests.filter((request) => /^https?:/i.test(request));
if (remoteRequests.length) failures.push(`external network requests observed: ${remoteRequests.join(', ')}`);
const tree = await call('Accessibility.getFullAXTree');
const unnamed = tree.nodes.filter((node) => ['link', 'button'].includes(node.role?.value) && !node.name?.value).length;
if (unnamed) failures.push(`accessibility tree contains ${unnamed} unnamed links or buttons`);
socket.close();

if (failures.length) {
  console.error(`Offline report browser validation failed (${failures.length}):\n- ${failures.join('\n- ')}`);
  process.exit(1);
}
console.log('Offline report browser validation passed at 375px and 1440px: keyboard navigation, no-script content, contrast, terminal/diff layout, accessibility names, and zero external requests.');
