import { readFile, writeFile } from 'node:fs/promises';

const counterPath = process.env.PLAYTESTR_FLAKY_FILE;
if (!counterPath) throw new Error('PLAYTESTR_FLAKY_FILE is required');
let previous = 0;
try { previous = Number(await readFile(counterPath, 'utf8')) || 0; } catch { /* first run */ }
const attempt = previous + 1;
await writeFile(counterPath, String(attempt));
console.log(`FLAKY ATTEMPT ${attempt}`);
setTimeout(() => process.exit(attempt % 2 === 1 ? 7 : 0), 100);
