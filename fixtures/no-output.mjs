#!/usr/bin/env node

process.stdin.setRawMode?.(true);
process.stdin.resume();
process.stdin.on('data', data => {
  if (data.includes(3)) process.exit(0);
});
setInterval(() => undefined, 1000);
