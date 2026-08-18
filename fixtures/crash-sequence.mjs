#!/usr/bin/env node

process.stdout.write('CRASH FIXTURE\nPress x to trigger the intentional failure.\n');
process.stdin.setRawMode?.(true);
process.stdin.resume();
process.stdin.setEncoding('utf8');
process.stdin.on('data', data => {
  if (data.includes('x')) process.exit(2);
  if (data.includes('\u0003')) process.exit(0);
});
