#!/usr/bin/env node

let turn = 0;
process.stdout.write('\x1b[2J\x1b[HTERMINAL QUEST\nPress Enter to advance. Press q to quit.\nTURN 0\n');
process.stdin.setRawMode?.(true);
process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', data => {
  if (data.includes('q') || data.includes('\u0003')) {
    process.stdin.setRawMode?.(false);
    process.exit(0);
  }
  if (data === '\r' || data === '\n' || data === ' ') {
    turn += 1;
    process.stdout.write(`\x1b[2J\x1b[HTERMINAL QUEST\nPress Enter to advance. Press q to quit.\nTURN ${turn}\n`);
  }
});
