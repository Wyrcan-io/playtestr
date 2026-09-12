import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs';
import { dirname, join, normalize, relative, resolve, sep } from 'node:path';
import { gzipSync } from 'node:zlib';

const output = resolve(process.argv[2] || 'public');
const repository = resolve('.');
const failures = [];
const requiredRoutes = [
  'index.html', '404.html', 'download/index.html', 'docs/index.html',
  'docs/installation/index.html', 'docs/writing-tests/index.html',
  'docs/snapshots/index.html', 'docs/troubleshooting/index.html',
  'docs/spec-v1/index.html', 'docs/report-v1/index.html',
  'docs/compatibility/index.html', 'docs/platform-evidence/index.html',
  'docs/terminal-compatibility/index.html', 'examples/index.html',
  'releases/index.html', 'releases/v0.1.0/index.html',
  'support/index.html', 'trials/index.html', 'index.json',
  'demos/terminal-demo.json', 'schema/playtestr-spec-v1.schema.json',
  'schema/playtestr-report-v1.schema.json', 'images/social-preview.png'
];

const fail = (message) => failures.push(message);
for (const route of requiredRoutes) if (!existsSync(join(output, route))) fail(`missing required output: ${route}`);
const walk = (directory) => readdirSync(directory).flatMap((name) => {
  const path = join(directory, name);
  return statSync(path).isDirectory() ? walk(path) : [path];
});
const files = existsSync(output) ? walk(output) : [];
const htmlFiles = files.filter((file) => file.endsWith('.html'));
const idsByFile = new Map();
const pageTitles = new Set();

for (const file of htmlFiles) {
  const html = readFileSync(file, 'utf8');
  const label = relative(output, file);
  const title = html.match(/<title>([^<]+)<\/title>/i)?.[1];
  if (!title) fail(`${label}: missing title`);
  else if (pageTitles.has(title)) fail(`${label}: duplicate page title ${title}`);
  else pageTitles.add(title);
  if (!/<meta name=description content="[^"]+"|<meta name="description" content="[^"]+"/i.test(html)) fail(`${label}: missing description`);
  if (!/<link rel=canonical href=/i.test(html)) fail(`${label}: missing canonical URL`);
  if (!/https:\/\/wyrcan-io\.github\.io\/playtestr\//i.test(html.match(/<link rel=canonical href=([^\s>]+)/i)?.[1] || '')) fail(`${label}: canonical URL does not use the Pages project path`);
  if (!/og:image/i.test(html)) fail(`${label}: missing social preview metadata`);
  idsByFile.set(file, new Set([...html.matchAll(/\sid=(?:"([^"]+)"|'([^']+)'|([^\s>]+))/gi)].map((match) => match[1] || match[2] || match[3])));
}

const decode = (value) => value.replace(/&amp;/g, '&');
const resolveSiteTarget = (sourceFile, raw) => {
  const target = decode(raw).split('?')[0];
  if (!target || target.startsWith('#') || /^(?:https?:|mailto:|tel:|data:)/i.test(target)) return null;
  const [pathPart, fragment = ''] = target.split('#');
  let sitePath;
  if (pathPart.startsWith('/playtestr/')) sitePath = pathPart.slice('/playtestr/'.length);
  else if (pathPart === '/playtestr') sitePath = '';
  else if (pathPart.startsWith('/')) return {externalRoot: true, raw};
  else sitePath = relative(output, normalize(join(dirname(sourceFile), pathPart)));
  if (sitePath.endsWith('/')) sitePath += 'index.html';
  if (!sitePath || sitePath === '.') sitePath = 'index.html';
  return {file: resolve(output, sitePath), fragment, raw};
};

for (const file of htmlFiles) {
  const html = readFileSync(file, 'utf8');
  for (const match of html.matchAll(/\s(?:href|src)=(?:"([^"]+)"|'([^']+)'|([^\s>]+))/gi)) {
    const raw = match[1] || match[2] || match[3];
    const target = resolveSiteTarget(file, raw);
    if (!target) continue;
    if (target.externalRoot) { fail(`${relative(output, file)}: root URL escapes /playtestr/: ${raw}`); continue; }
    if (!existsSync(target.file)) { fail(`${relative(output, file)}: broken local target ${raw}`); continue; }
    if (target.fragment && target.file.endsWith('.html')) {
      const ids = idsByFile.get(target.file) || new Set();
      if (!ids.has(decodeURIComponent(target.fragment))) fail(`${relative(output, file)}: missing fragment ${raw}`);
    }
  }
}

try {
  const search = JSON.parse(readFileSync(join(output, 'index.json'), 'utf8'));
  for (const term of ['installation', 'expect_not', 'snapshots', 'cleanup']) {
    if (!search.some((page) => `${page.title} ${page.text}`.toLowerCase().includes(term))) fail(`search index does not contain ${term}`);
  }
} catch (error) { fail(`invalid search index: ${error.message}`); }

try {
  const demo = JSON.parse(readFileSync(join(output, 'demos/terminal-demo.json'), 'utf8'));
  if (demo.schemaVersion !== 1 || !Array.isArray(demo.scenarios) || demo.scenarios.length !== 2) fail('demo must contain schema v1 and two scenarios');
  const expected = readFileSync(join(repository, 'examples/snapshots/diagnostics.txt'), 'utf8').replace(/\r\n/g, '\n');
  const failure = demo.scenarios.find((item) => item.id === 'failure');
  if (`${failure?.evidence?.expected}\n` !== expected) fail('demo expected evidence differs from reviewed diagnostics snapshot');
  if (!failure?.evidence?.diff?.includes('Preview deployed successfully.')) fail('demo failure lacks the verified mismatch');
} catch (error) { fail(`invalid terminal demonstration: ${error.message}`); }

const releaseData = readFileSync(join(repository, 'site/data/release.toml'), 'utf8');
const releaseRecord = readFileSync(join(repository, 'docs/releases/v0.1.0.md'), 'utf8');
const readme = readFileSync(join(repository, 'README.md'), 'utf8');
for (const match of releaseData.matchAll(/archive = "([^"]+)"[\s\S]*?sha256 = "([a-f0-9]{64})"/g)) {
  const [, archive, hash] = match;
  if (!releaseRecord.includes(archive) || !readme.includes(archive)) fail(`release archive is inconsistent across public sources: ${archive}`);
  if (!releaseRecord.includes(hash)) fail(`release hash is absent from the release record: ${archive}`);
}

const markdownFiles = [
  ...readdirSync(repository)
    .filter((name) => name.endsWith('.md'))
    .map((name) => join(repository, name)),
  ...walk(join(repository, 'docs')).filter((file) => file.endsWith('.md'))
];
for (const file of markdownFiles) {
  const markdown = readFileSync(file, 'utf8');
  for (const match of markdown.matchAll(/!?\[[^\]]*\]\(([^)]+)\)/g)) {
    let target = match[1].trim();
    if (target.startsWith('<')) target = target.slice(1, target.indexOf('>'));
    else target = target.split(/\s+["']/)[0];
    target = target.split('#')[0].split('?')[0];
    if (!target || /^(?:https?:|mailto:|tel:|data:)/i.test(target)) continue;
    let decoded;
    try { decoded = decodeURIComponent(target); }
    catch { fail(`${relative(repository, file)}: malformed local Markdown link ${target}`); continue; }
    const destination = decoded.startsWith('/') ? resolve(repository, `.${decoded}`) : resolve(dirname(file), decoded);
    if (!existsSync(destination)) fail(`${relative(repository, file)}: broken local Markdown target ${target}`);
  }
}

const cssSource = readFileSync(join(repository, 'site/assets/style.css'), 'utf8');
for (const token of ['#fffdf9', '#252323', '#625e5c', '#d8d2cd', '#652d3c', '#292728']) if (!cssSource.includes(token)) fail(`missing locked color token ${token}`);
for (const prohibited of [/backdrop-filter/i, /linear-gradient/i, /radial-gradient/i, /filter:\s*blur/i]) if (prohibited.test(cssSource)) fail(`prohibited visual effect found: ${prohibited}`);
const rgb = (hex) => [1, 3, 5].map((index) => Number.parseInt(hex.slice(index, index + 2), 16) / 255).map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4);
const contrast = (foreground, background) => { const a = rgb(foreground).reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0); const b = rgb(background).reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0); return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05); };
for (const [foreground, background, label] of [['#252323', '#fffdf9', 'body text'], ['#625e5c', '#fffdf9', 'muted text'], ['#652d3c', '#fffdf9', 'rust links'], ['#eee9e4', '#292728', 'terminal text'], ['#bfcca1', '#292728', 'terminal pass text']]) if (contrast(foreground, background) < 4.5) fail(`${label} color contrast is below 4.5:1`);

const initialAssets = files.filter((file) => /\.(?:css|js)$/.test(file) && !file.includes(`terminal-demo${sep}`));
const compressedCode = initialAssets.reduce((sum, file) => sum + gzipSync(readFileSync(file)).length, 0);
if (compressedCode > 100 * 1024) fail(`shared CSS and JavaScript exceed 100 KB compressed: ${compressedCode}`);
const homeSize = gzipSync(readFileSync(join(output, 'index.html'))).length + compressedCode;
if (homeSize > 500 * 1024) fail(`home first-load budget exceeds 500 KB compressed: ${homeSize}`);

if (failures.length) {
  console.error(`Website validation failed (${failures.length}):\n- ${failures.join('\n- ')}`);
  process.exit(1);
}
console.log(`Website validation passed: ${htmlFiles.length} HTML pages, ${compressedCode} compressed code bytes, ${homeSize} compressed home bytes.`);
