#!/usr/bin/env node

import { loadManifest, PlaytestRunner } from '../dist/index.js';

const runs = Number(process.argv[2] ?? 100);
if (!Number.isSafeInteger(runs) || runs <= 0) {
  console.error('Run count must be a positive safe integer.');
  process.exit(1);
}

const manifest = await loadManifest('fixtures/turn-counter.json');
for (let index = 0; index < runs; index += 1) {
  const report = await new PlaytestRunner().run(manifest, {
    actions: [{ key: 'q', waitMs: 10 }],
    maxActions: 1,
    maxElapsedMs: 4000,
  });
  const acceptable = report.status === 'passed' &&
    report.termination.kind === 'target-exit' &&
    !report.findings.some(finding => finding.kind === 'runner-error');
  if (!acceptable) {
    console.error(`Lifecycle soak failed on run ${index + 1}: ${JSON.stringify(report.termination)}`);
    process.exit(1);
  }
}

console.log(`Lifecycle soak passed: ${runs}/${runs} clean runs.`);
await new Promise(resolve => setTimeout(resolve, process.platform === 'win32' ? 1500 : 100));
const activeHandles = process._getActiveHandles()
  .filter(handle => handle !== process.stdin && handle !== process.stdout && handle !== process.stderr)
  .map(handle => ({
    type: handle.constructor?.name,
    pid: handle.pid,
    fd: handle.fd,
    readable: handle.readable,
    writable: handle.writable,
  }));
console.log(`Remaining native handles: ${JSON.stringify(activeHandles)}`);
if (activeHandles.length > 0) process.exit(1);
process.exitCode = 0;
